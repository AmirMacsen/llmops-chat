import collections
from uuid import UUID

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document as LCDocument
from langchain_core.retrievers import BaseRetriever
from pydantic import Field

from pkg.sqlalchemy import SQLAlchemy
from internal.service import JiebaService
from internal.model import KeywordTable, Segment


class FullTextRetriever(BaseRetriever):
    """全文检索器"""
    db: SQLAlchemy
    jieba_service: JiebaService
    dataset_ids: list[UUID]
    search_kwargs: dict=Field(default_factory=dict)

    def _get_relevant_documents(
            self, query: str, *,
            run_manager: CallbackManagerForRetrieverRun
    ) -> list[LCDocument]:
        """根据传递的query执行关键词检索"""
        keywords = self.jieba_service.extract_keywords(query, 10)

        # 查询关键词列表
        keyword_tables = [
                keyword_table for keyword_table, in self.db.session.query(KeywordTable.keyword_table).filter(
                KeywordTable.dataset_id.in_(self.dataset_ids),
            ).all()
        ]

        # 遍历所有的知识库关键词表，找到匹配query关键词的id列表
        all_ids = []

        for keyword_table in keyword_tables:
            for keyword, segment_ids in keyword_table.items():
                if keyword in keywords:
                    all_ids.extend(segment_ids)

        # 统计document_id出现的次数
        segment_id_counts=collections.Counter(all_ids)
        # 获取频率最高的前k个数据
        k = self.search_kwargs.pop("k", 4)
        top_k_ids = segment_id_counts.most_common(k)

        # 根据得到的id列表检索数据库，得到片段列表数据
        segments=self.db.session.query(Segment).filter(
            Segment.id.in_([segment_id for segment_id, _ in top_k_ids]),
        ).all()

        segments_dict = {
            str(segment.id): segment for segment in segments
        }

        # 根据频率进行排序
        sorted_segment=[segments_dict[str(id)] for id, freq in top_k_ids if id in segments_dict]

        # 转化为lc文档列表
        lc_documents = [LCDocument(
            page_content=segment.content,
            metadata={
                "account_id": str(segment.account_id),
                "dataset_id": str(segment.dataset_id),
                "document_id": str(segment.document_id),
                "segment_id": str(segment.id),
                "node_id": str(segment.node_id),
                "document_enabled": True,
                "segment_enabled": True,
                "score": 0
            }
        ) for segment in sorted_segment]

        return lc_documents
