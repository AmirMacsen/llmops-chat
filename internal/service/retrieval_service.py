from uuid import UUID

from flask import Flask
from injector import inject
from dataclasses import dataclass

from langchain_core.documents import Document as LCDocument
from langchain.retrievers import EnsembleRetriever
from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, Field
from sqlalchemy import update

from internal.entity.dataset_entity import RetrievalStrategy, RetrievalSource
from internal.exception import NotFoundException
from internal.model import Dataset, DatasetQuery, Segment
from internal.service.base_service import BaseService
from pkg.sqlalchemy import SQLAlchemy
from .vector_database_service import VectorDatabaseService
from .jieba_service import JiebaService
from ..core.agent.entities.agent_entity import DATASET_RETRIEVAL_TOOL_NAME
from ..lib.helper import combine_documents


@inject
@dataclass
class RetrievalService(BaseService):
    """知识库检索服务"""
    db: SQLAlchemy
    vector_database_service: VectorDatabaseService
    jieba_service: JiebaService

    def search_in_datasets(self,
                         dataset_ids: list[UUID],
                         query: str,
                         account_id: UUID,
                         retrieval_strategy: str=RetrievalStrategy.SEMANTIC,
                         k: int=4,
                         score: float=0,
                         retrieval_source:str = RetrievalSource.HIT_TESTING) -> list[LCDocument]:
        """根据检索策略进行检索"""
        account_id = str(account_id)

        # 提取知识库列表进行校验
        datasets = self.db.session.query(Dataset).filter(
            Dataset.id.in_(dataset_ids),
            Dataset.account_id == account_id,
        ).all()
        if datasets is None or len(datasets) == 0:
            raise NotFoundException("知识库不存在")

        dataset_ids = [dataset.id for dataset in datasets]

        # 构建不同种类的检索器
        from internal.core.retrievers import SemanticRetriever, FullTextRetriever
        semantic_retriever = SemanticRetriever(
            dataset_ids=dataset_ids,
            vector_store=self.vector_database_service.vector_store,
            search_kwargs={
                "k": k,
                "score_threshold": score,
            }
        )
        full_text_retriever = FullTextRetriever(
            dataset_ids=dataset_ids,
            jieba_service=self.jieba_service,
            db=self.db,
            search_kwargs={
                "k": k,
            }
        )

        hybrid_retriever = EnsembleRetriever(
            retrievers=[semantic_retriever, full_text_retriever],
            weights=[0.5, 0.5],
        )

        # 根据不同的检索策略执行检索
        if retrieval_strategy == RetrievalStrategy.SEMANTIC:
            lc_documents =  semantic_retriever.invoke(query)[:k]
        elif retrieval_strategy == RetrievalStrategy.FULL_TEXT:
            lc_documents =  full_text_retriever.invoke(query)[:k]
        elif retrieval_strategy == RetrievalStrategy.HYBRID:
            lc_documents =  hybrid_retriever.invoke(query)[:k]
        else:
            raise NotFoundException("检索策略不存在")

        # 添加知识库查询记录
        unique_dataset_ids = list(set(str(lc_document.metadata["dataset_id"]) for lc_document in lc_documents))
        for dataset_id in unique_dataset_ids:
            self.create(
                DatasetQuery,
                dataset_id=dataset_id,
                query=query,
                source=retrieval_source,
                source_app_id=None,
                created_by=account_id,
            )

        # 批量更新片段的命中次数
        with self.db.auto_commit():
            stmt = (
                update(Segment)
                .where(Segment.id.in_([lc_document.metadata["segment_id"] for lc_document in lc_documents]))
                .values(hit_count=Segment.hit_count + 1)
            )
            self.db.session.execute(stmt)

        return lc_documents


    def create_langchain_tool_from_search(
            self,
            flask_app: Flask,
            dataset_ids: list[UUID],
            query: str,
            account_id: UUID,
            retrieval_strategy: str = RetrievalStrategy.SEMANTIC,
            k: int = 4,
            score: float = 0,
            retrieval_source: str = RetrievalSource.HIT_TESTING

    ) -> BaseTool:
        """创建langchain工具"""
        class DatasetRetrievalInput(BaseModel):
            query: str = Field(..., description="查询内容")

        @tool(DATASET_RETRIEVAL_TOOL_NAME, args_schema=DatasetRetrievalInput)
        def dataset_retrieval(query: str) -> str:
            """当你觉得用户的提问已经超过知识库范畴，可以调用该工具，输入为搜索的query语句，返回数据为检索内容"""
            # 1.调用search_in_datasets检索得到LangChain文档列表
            with flask_app.app_context():
                documents = self.search_in_datasets(
                    dataset_ids=dataset_ids,
                    query=query,
                    account_id=account_id,
                    retrieval_strategy=retrieval_strategy,
                    k=k,
                    score=score,
                    retrieval_source=retrieval_source,
                )

            # 2.将LangChain文档列表转换成字符串后返回
            if len(documents) == 0:
                return "知识库内没有检索到对应内容"

            return combine_documents(documents)

        return dataset_retrieval