import logging
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, current_app
from injector import inject
from langchain_core.documents import Document as LCDocument
from sqlalchemy import func
from redis import Redis
from weaviate.classes.query import Filter

from internal.core.file_extractor import FileExtractor
from internal.entity.cache_entity import LOCK_DOCUMENT_UPDATE_ENABLED, LOCK_KEYWORD_TABLE_UPDATE_KEYWORD_TABLE, \
    LOCK_EXPIRE
from internal.entity.dataset_entity import DocumentStatus, SegmentStatus
from internal.exception import NotFoundException
from internal.lib.helper import generate_text_hash
from internal.model import Document, Segment, KeywordTable, DatasetQuery
from internal.service import EmbeddingsService
from internal.service.base_service import BaseService
from internal.service.jieba_service import JiebaService
from internal.service.keyword_table_service import KeywordTableService
from internal.service.process_rule_service import ProcessRuleService
from internal.service.vector_database_service import VectorDatabaseService
from pkg.sqlalchemy import SQLAlchemy


@inject
@dataclass
class IndexingService(BaseService):
    """索引服务"""

    db: SQLAlchemy
    file_extractor: FileExtractor
    process_rule_service: ProcessRuleService
    embedding_service: EmbeddingsService
    jieba_service: JiebaService
    keyword_table_service: KeywordTableService
    vector_database_service: VectorDatabaseService
    redis_client: Redis

    def build_documents(self, document_ids:list[UUID]) -> None:
        """根据文档id构建Document"""

        # 根据传递的文档id获取所有文档
        documents = self.db.session.query(Document).filter(
            Document.id.in_(document_ids)).all()

        # 遍历文档
        for document in documents:
            try:
                # 更新当前状态为解析中，并记录开始处理时间
                self.update(
                    document,
                    status=DocumentStatus.PARSING,
                    processing_started_at=datetime.now(),
                )
                # 执行文档加载步骤，并更新文档状态和时间
                lc_documents = self._parsing(document)
                print("文档预处理结束")
                # 执行文档分割步骤，并更新文档状态和时间，segment信息也要修改
                lc_segments = self._splitting(document, lc_documents)
                print("文档分割结束")
                # 执行文档索引构建，涵盖关键词提取、向量，并更新数据状态
                self._indexing(document, lc_segments)
                print("文档索引构建结束")
                # 存储操作，涵盖文档状态更新和向量数据库存储
                self._complete(document, lc_segments)
                print("文档存储结束")
            except Exception as e:
                logging.exception(f"构建文档发生错误，错误信息： {str(e)}")
                # 更新文档状态
                self.update(
                    document,
                    status=DocumentStatus.ERROR,
                    error=str(e),
                    stopped_at=datetime.now(),
                )


    def update_document_enabled(self, document_id:UUID) -> None:
        """根据传递的文档id更新文档状态+向量库"""
        # 构建缓存键
        cache_key = LOCK_DOCUMENT_UPDATE_ENABLED.format(document_id=document_id)

        # 根据传递的document id获取文档记录
        document = self.get(Document, document_id)
        if not document:
            logging.exception(f"当前文档不存在，文档id: {document_id}")
            raise NotFoundException("文档不存在")

        # 查找当前归属于文档的所有片段节点ID
        segments = self.db.session.query(Segment.id, Segment.node_id, Segment.enabled).filter(
            Segment.document_id == document_id,
            Segment.status == SegmentStatus.COMPLETED
        ).all()
        segment_ids = [
            segment_id for segment_id,_, _ in segments
        ]
        node_ids = [
            node_id for _, node_id, _ in segments
        ]
        # 执行循环遍历所有node_ids并更新向量数据库
        try:
            connect = self.vector_database_service.collection
            for node_id in node_ids:
                try:
                    connect.data.update(
                        uuid=node_id,
                        properties={
                            "document_enabled": document.enabled
                        }
                    )
                except Exception as e:
                    with self.db.auto_commit():
                        self.db.session.query(Segment).filter(
                            Segment.node_id == node_id
                        ).update({
                            "status": SegmentStatus.ERROR,
                            "error": str(e),
                            "stopped_at": datetime.now(),
                            "enabled": False,
                            "disabled_at": datetime.now()
                        })

            # 更新关键词表对应的数据（enabled为false表示从关键词表中删除数据，enabled为true表示从关键词表中新增数据）
            if document.enabled is True:
                # 从禁用改为启用, 需要更新关键词表
                enabled_segment_ids = [id for id, _, enabled in segments if enabled is True]
                self.keyword_table_service.add_keyword_table_from_ids(document.dataset_id, enabled_segment_ids)
            else:
                # 从启用改为禁用, 需要剔除关键词
                self.keyword_table_service.delete_keyword_table_from_ids(document.dataset_id, segment_ids)

        except Exception as e:
            logging.exception(f"更新文档向量库发生错误，错误信息： {str(e)}")
            # 修改状态为原来的状态
            _enabled = not document.enabled
            self.update(
                document,
                enabled=_enabled,
                disabled_at=None if _enabled else datetime.now(),
            )
        finally:
            self.redis_client.delete(cache_key)

    def _parsing(self, document:Document) -> list[LCDocument]:
        """解析文档"""
        upload_file=document.upload_file
        lc_documents = self.file_extractor.load(upload_file, False, True)

        # 循环处理langchain文档
        for lc_document in lc_documents:
            lc_document.page_content = self._clean_extra_text(lc_document.page_content)

        self.update(document, status=DocumentStatus.SPLITTING,
                    parsing_completed_at=datetime.now(),
                    character_count=sum([len(lc_document.page_content) for lc_document in lc_documents]))

        return lc_documents

    def _splitting(self, document:Document, lc_documents:list[LCDocument]) -> list[LCDocument]:
        """文档分割"""
        process_rule = document.process_rule
        text_splitter = self.process_rule_service.get_text_splitter_by_process_rule(
            process_rule=process_rule,
            length_function=self.embedding_service.calculate_token_count
        )
        for lc_document in lc_documents:
            lc_document.page_content = self.process_rule_service.clean_text_by_process_rule(
                text=lc_document.page_content,
                process_rule=process_rule,
            )

        lc_segments = text_splitter.split_documents(lc_documents)

        # 获取对应文档的最大片段位置
        position = self.db.session.query(func.coalesce(func.max(Segment.position), 0)).filter(
            Segment.document_id == document.id
        ).scalar()

        # 循环处理片段数据并添加元数据，存储
        segments= []
        for lc_segment in lc_segments:
            position += 1
            content = lc_segment.page_content
            segment = self.create(
                Segment,
                account_id=document.account_id,
                dataset_id=document.dataset_id,
                document_id=document.id,
                node_id=uuid.uuid4(),
                position=position,
                content=content,
                character_count=len(content),
                token_count=self.embedding_service.calculate_token_count(content),
                hash=generate_text_hash(content),
                status=SegmentStatus.WAITING,
            )

            lc_segment.metadata = {
                "account_id": str(document.account_id),
                "dataset_id": str(document.dataset_id),
                "document_id": str(document.id),
                "segment_id": str(segment.id),
                "node_id": str(segment.node_id),
                "document_enabled": False,
                "segment_enabled": False,
            }

            segments.append(segment)

        # 更新文档的数据
        self.update(
            document,
            token_count=sum([segment.token_count for segment in segments]),
            status=DocumentStatus.INDEXING,
            splitting_completed_at=datetime.now(),
        )
        return lc_segments

    def _indexing(self, document:Document, lc_segments:list[LCDocument]) -> None:
        """索引构建"""
        for lc_segment in lc_segments:
            # 提取关键词，关键词的数量不超过10个
            keywords = self.jieba_service.extract_keywords(lc_segment.page_content, 10)
            # 更新文档的关键词
            self.db.session.query(Segment).filter(
                Segment.id == lc_segment.metadata["segment_id"]
            ).update({"keywords": keywords,
                      "status": SegmentStatus.INDEXING,
                      "indexing_completed_at": datetime.now(),
                      })

            # 获取当前知识库的关键词词表
            keyword_table_record = self.keyword_table_service.get_keyword_table_from_dataset(document.dataset_id)

            keyword_table = {
                field: set(value)
                for field, value in keyword_table_record.keyword_table.items()
            }
            # 将新关键词添加到词表中
            for keyword in keywords:
                if keyword not in keyword_table:
                    keyword_table[keyword] = set()
                keyword_table[keyword].add(lc_segment.metadata["segment_id"])

            # 更新关键词表，确保所有值都是list类型而不是set类型
            keyword_table_for_update = {}
            for field, value in keyword_table.items():
                keyword_table_for_update[field] = list(value)

            self.update(
                keyword_table_record,
                keyword_table=keyword_table_for_update
            )

        # 更新文档数据
        self.update(
            document,
            indexing_completed_at=datetime.now(),
        )


    def _complete(self, document:Document, lc_segments:list[LCDocument]) -> None:
        """完成构建"""
        # 循环遍历片段列表数据，将文档和片段状态修改为可用
        for lc_segment in lc_segments:
            lc_segment.metadata["document_enabled"] = True
            lc_segment.metadata["segment_enabled"] = True

        # 调用向量数据库，每次存储10条数据
        def thread_function(flask_app:Flask, chunks:list[LCDocument], ids:list[UUID])-> None:
            """线程函数，执行向量数据库和pg数据库存储"""
            with flask_app.app_context():
                try:
                    # 调用向量数据库存储
                    self.vector_database_service.vector_store.add_documents(
                        chunks,
                        ids=ids,
                    )
                    # 更新片段数据
                    with self.db.auto_commit():
                        self.db.session.query(Segment).filter(
                            Segment.node_id.in_(ids)
                        ).update({
                            "status": SegmentStatus.COMPLETED,
                            'completed_at': datetime.now(),
                            "enabled": True
                        })
                except Exception as e:
                    logging.exception(f"构建索引失败，错误信息：{str(e)}")
                    with self.db.auto_commit():
                        self.db.session.query(Segment).filter(
                            Segment.node_id.in_(ids)
                        ).update({
                            "status": SegmentStatus.ERROR,
                            'completed_at': None,
                            "stopped_at": datetime.now(),
                            "enabled": False
                        })

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for i in range(0, len(lc_segments), 10):
                chunks = lc_segments[i:i + 10]
                ids = [chunk.metadata["node_id"] for chunk in chunks]
                futures.append(executor.submit(thread_function, current_app._get_current_object(), chunks, ids))

            for future in futures:
                future.result()

        # 更新文档数据
        self.update(
            document,
            status=DocumentStatus.COMPLETED,
            completed_at=datetime.now(),
            enabled=True,
        )


    def delete_document(self, dataset_id:UUID, document_id:UUID)->None:
        """根据dataset_id和document_id删除文档"""
        # 查找该文档下的文档片段
        segment_ids = [
            str(id) for id, in self.db.session.query(Segment.id).filter(
                Segment.document_id == document_id
            ).all()
        ]
        # 调用向量数据库删除关联记录
        connection = self.vector_database_service.collection
        connection.data.delete_many(
            where=Filter.by_property("document_id").equal(document_id)
        )
        # 删除pg中的数据
        with self.db.auto_commit():
            self.db.session.query(Segment).filter(
                Segment.document_id == document_id
            ).delete()

        # 删除关键词表数据和向量数据库中的数据
        self.keyword_table_service.delete_keyword_table_from_ids(dataset_id, segment_ids)

    def delete_dataset(self, dataset_id: UUID) -> None:
        """根据传递的知识库id执行相应的删除操作"""
        try:
            with self.db.auto_commit():
                # 1.删除关联的文档记录
                self.db.session.query(Document).filter(
                    Document.dataset_id == dataset_id,
                ).delete()

                # 2.删除关联的片段记录
                self.db.session.query(Segment).filter(
                    Segment.dataset_id == dataset_id,
                ).delete()

                # 3.删除关联的关键词表记录
                self.db.session.query(KeywordTable).filter(
                    KeywordTable.dataset_id == dataset_id,
                ).delete()

                # 4.删除知识库查询记录
                self.db.session.query(DatasetQuery).filter(
                    DatasetQuery.dataset_id == dataset_id,
                ).delete()

            # 5.调用向量数据库删除知识库的关联记录
            self.vector_database_service.collection.data.delete_many(
                where=Filter.by_property("dataset_id").equal(str(dataset_id))
            )
        except Exception as e:
            logging.exception(f"异步删除知识库关联内容出错, dataset_id: {dataset_id}, 错误信息: {str(e)}")

    @classmethod
    def _clean_extra_text(cls, text: str) -> str:
        """清除过滤传递的多余空白字符串"""
        text = re.sub(r'<\|', '<', text)
        text = re.sub(r'\|>', '>', text)
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F\xEF\xBF\xBE]', '', text)
        text = re.sub('\uFFFE', '', text)  # 删除零宽非标记字符
        return text


