import logging
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from injector import inject
from redis import Redis
from sqlalchemy import UUID, asc, func
from langchain_core.documents import Document as LCDocument

from internal.entity.cache_entity import LOCK_EXPIRE, LOCK_SEGMENT_UPDATE_ENABLED
from internal.entity.dataset_entity import SegmentStatus, DocumentStatus
from internal.exception import ValidationException, NotFoundException, FailedException
from internal.model import Segment, Document
from internal.schema.segment_schema import GetSegmentWithPageRequest, CreateSegmentRequest, UpdateSegmentRequest
from internal.service.base_service import BaseService
from internal.service.keyword_table_service import KeywordTableService
from internal.service.vector_database_service import VectorDatabaseService
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy
from .embeddings_service import EmbeddingsService
from .jieba_service import JiebaService
from ..lib.helper import generate_text_hash


@inject
@dataclass
class SegmentService(BaseService):
    """片段服务"""
    db: SQLAlchemy
    redis_client: Redis
    keyword_table_service: KeywordTableService
    vector_database_service: VectorDatabaseService
    embeddings_service: EmbeddingsService
    jieba_service: JiebaService

    def get_segment_with_page(self, dataset_id: UUID, document_id: UUID, req: GetSegmentWithPageRequest) -> tuple[
        list[Segment], Paginator]:
        """获取指定知识库文档的片段列表"""
        # todo: 权限验证
        account_id = "b03d55b5-895e-47c8-b767-6d0015ae60a1"
        document = self.get(Document, document_id)
        if document is None or document.dataset_id != dataset_id or str(document.account_id) != account_id:
            raise NotFoundException("该文档不存在")

        # 构建分页查询器
        paginator = Paginator(db=self.db, req=req)

        filters = [Segment.document_id == document_id]
        if req.search_word.data:
            filters.append(Segment.content.ilike(f"%{req.search_word.data}%"))

        segments = paginator.paginate(
            self.db.session.query(Segment).filter(*filters).order_by(asc("position"))
        )

        return segments, paginator

    def get_segment(self, dataset_id: UUID, document_id: UUID, segment_id: UUID) -> Segment | None:
        """获取指定的文档片段信息"""
        # todo: 权限验证
        account_id = "b03d55b5-895e-47c8-b767-6d0015ae60a1"
        document = self.get(Document, document_id)
        if document is None or document.dataset_id != dataset_id or str(document.account_id) != account_id:
            raise NotFoundException("该文档不存在")

        segment = self.get(Segment, segment_id)
        if (
                segment is None
                or str(segment.account_id) != account_id
                or segment.document_id != document_id
                or segment.document_id != document_id
        ):
            raise NotFoundException("该片段不存在")
        return segment

    def update_segment_enabled(self, dataset_id: UUID, document_id: UUID, segment_id: UUID, enabled: bool) -> None:
        """根据传递的信息更新指定的文档片段启用状态"""
        account_id = "b03d55b5-895e-47c8-b767-6d0015ae60a1"

        # 获取片段信息并校验权限
        segment = self.get(Segment, segment_id)
        if (
                segment is None
                or str(segment.account_id) != account_id
                or segment.document_id != document_id
                or segment.document_id != document_id
        ):
            raise NotFoundException("该片段不存在")

        # 判断状态是否已经完成，只有complete状态才能修改
        if segment.status != SegmentStatus.COMPLETED:
            raise ValidationException("该片段未完成，请等待完成")

        # 可以修改判断是否需要修改，如果与数据库一致，则不需要修改
        if segment.enabled == enabled:
            raise ValidationException("该片段已处于该状态")

        # 获取锁并进行修改
        cache_key = LOCK_SEGMENT_UPDATE_ENABLED.format(segment_id=segment_id)
        cache_result = self.redis_client.get(cache_key)
        if cache_result is not None:
            raise FailedException(f"segment更新锁已经被占用，segment_id: {segment_id}")

        # 上锁并更新 pg + vector
        with self.redis_client.lock(cache_key, timeout=LOCK_EXPIRE):
            try:
                # 修改pg
                self.update(
                    segment,
                    enabled=enabled,
                    disabled_at=datetime.now() if not enabled else None,
                )
                # 更新关键词表
                document = segment.document
                if enabled and document.enabled:
                    self.keyword_table_service.add_keyword_table_from_ids(dataset_id, [str(segment_id)])
                else:
                    self.keyword_table_service.delete_keyword_table_from_ids(dataset_id, [str(segment_id)])

                # 同步处理weaviate中的数据
                self.vector_database_service.collection.data.update(
                    uuid=segment.node_id,
                    properties={
                        "enabled": enabled
                    }
                )
            except Exception as e:
                import traceback
                traceback.print_exc()
                logging.exception(f"更改文档片段启用状态发生异常，segment_id:{segment_id}")
                self.update(
                    segment,
                    error=str(e),
                    status=SegmentStatus.ERROR,
                    enabled=False,
                    disabled_at=datetime.now(),
                )
                raise FailedException(f"更改文档片段启用状态发生异常，segment_id:{segment_id}")

    def create_segment(self, dataset_id: UUID, document_id: UUID, request: CreateSegmentRequest) -> None:
        """根据传递的信息创建知识库文档片段"""
        account_id = "b03d55b5-895e-47c8-b767-6d0015ae60a1"

        # 校验上传内容的token总数不能超过1000
        token_count = self.embeddings_service.calculate_token_count(request.content.data)

        if token_count > 1000:
            raise ValidationException("上传内容不能超过1000个token")

        # 获取文档信息
        document = self.get(Document, document_id)
        if document is None or document.dataset_id != dataset_id or str(document.account_id) != account_id:
            raise NotFoundException("该文档不存在")

        # 判断文档的状态是否可以新增，如果不是构建完成，则不能新增
        if document.status != DocumentStatus.COMPLETED:
            raise ValidationException("该文档未完成，请等待完成")

        # 提取文档片段的最大位置
        position = self.db.session.query(func.coalesce(func.max(Segment.position), 0)).filter(
            Segment.document_id == document_id
        ).scalar()

        # 检测是否传递了keywords，如果没有传递，则使用jieba服务生成
        if request.keywords.data is None or len(request.keywords.data) == 0:
            request.keywords.data = self.jieba_service.extract_keywords(request.content, 10)

        # 向pg数据库新增数据
        segment = None
        try:
            position += 1
            segment = self.create(
                Segment,
                account_id=account_id,
                dataset_id=dataset_id,
                document_id=document_id,
                node_id=str(uuid4()),
                position=position,
                content=request.content.data,
                keywords=request.keywords.data,
                character_count=len(request.content.data),
                token_count=token_count,
                hash=generate_text_hash(request.content.data),
                enabled=True,
                processing_started_at=datetime.now(),
                indexing_completed_at=datetime.now(),
                completed_at=datetime.now(),
                status=SegmentStatus.COMPLETED,
            )
            # 向量数据库中存储
            self.vector_database_service.vector_store.add_documents([LCDocument(
                page_content=request.content.data,
                metadata={
                    "account_id": str(document.account_id),
                    "dataset_id": str(document.dataset_id),
                    "document_id": str(document.id),
                    "segment_id": str(segment.id),
                    "node_id": str(segment.node_id),
                    "document_enabled": document.enabled,
                    "segment_enabled": True,
                }
            )],
                ids=[str(segment.node_id)]
            )

            # 重新计算片段的字符总数和token总数
            document_character_count, document_token_count = self.db.session.query(
                func.coalesce(func.sum(Segment.character_count), 0),
                func.coalesce(func.sum(Segment.token_count), 0)
            ).filter(
                Segment.document_id == document_id
            ).first()

            # 更新文档
            self.update(document, character_count=document_character_count, token_count=document_token_count)

            # 更新关键词表信息
            if document.enabled:
                self.keyword_table_service.add_keyword_table_from_ids(dataset_id, [str(segment.id)])
        except Exception as e:
            logging.exception(f"新增文档片段发生异常, 错误信息：{str(e)}")
            if segment:
                self.update(segment,
                            error=str(e),
                            status=SegmentStatus.ERROR,
                            enabled=False,
                            disabled_at=datetime.now(),
                            stopped_at=datetime.now())
            raise FailedException("新增文档片段失败")

    def update_segment(self, dataset_id: UUID, document_id: UUID, segment_id: UUID, request: UpdateSegmentRequest):
        """根据传递的信息更新指定的文档片段信息"""
        account_id = "b03d55b5-895e-47c8-b767-6d0015ae60a1"
        document = self.get(Document, document_id)
        if document is None or document.dataset_id != dataset_id or str(document.account_id) != account_id:
            raise NotFoundException("该文档不存在")

        segment = self.get(Segment, segment_id)
        if (
                segment is None
                or str(segment.account_id) != account_id
                or segment.document_id != document_id
                or segment.document_id != document_id
        ):
            raise NotFoundException("该片段不存在")

        if segment.status != SegmentStatus.COMPLETED:
            raise FailedException("当前片段不可修改状态，请稍后尝试")

            # 3.检测是否传递了keywords，如果没有传递的话，调用jieba服务生成关键词
        if request.keywords.data is None or len(request.keywords.data) == 0:
            request.keywords.data = self.jieba_service.extract_keywords(request.content.data, 10)

            # 4.计算新内容hash值，用于判断是否需要更新向量数据库以及文档详情
        new_hash = generate_text_hash(request.content.data)
        required_update = segment.hash != new_hash

        try:
            # 5.更新segment表记录
            self.update(
                segment,
                keywords=request.keywords.data,
                content=request.content.data,
                hash=new_hash,
                character_count=len(request.content.data),
                token_count=self.embeddings_service.calculate_token_count(request.content.data),
            )

            # 7.更新片段归属关键词信息
            self.keyword_table_service.delete_keyword_table_from_ids(dataset_id, [str(segment_id)])
            self.keyword_table_service.add_keyword_table_from_ids(dataset_id, [str(segment_id)])

            # 8.检测是否需要更新文档信息以及向量数据库
            if required_update:
                # 7.更新文档信息，涵盖字符总数、token总次数
                document = segment.document
                document_character_count, document_token_count = self.db.session.query(
                    func.coalesce(func.sum(Segment.character_count), 0),
                    func.coalesce(func.sum(Segment.token_count), 0)
                ).filter(Segment.document_id == document.id).first()
                self.update(
                    document,
                    character_count=document_character_count,
                    token_count=document_token_count,
                )

                # 9.更新向量数据库对应记录
                self.vector_database_service.collection.data.update(
                    uuid=str(segment.node_id),
                    properties={
                        "text": request.content.data,
                    },
                    vector=self.embeddings_service.embeddings.embed_query(request.content.data)
                )
        except Exception as e:
            logging.exception(f"更新文档片段记录失败, segment_id: {segment}, 错误信息: {str(e)}")
            raise FailedException("更新文档片段记录失败，请稍后尝试")

        return segment

    def delete_segment(self, dataset_id: UUID, document_id: UUID, segment_id: UUID):
        """根据传递的信息删除指定的片段"""
        account_id = "b03d55b5-895e-47c8-b767-6d0015ae60a1"
        document = self.get(Document, document_id)
        if document is None or document.dataset_id != dataset_id or str(document.account_id) != account_id:
            raise NotFoundException("该文档不存在")

        segment = self.get(Segment, segment_id)
        if (
                segment is None
                or str(segment.account_id) != account_id
                or segment.dataset_id != dataset_id
                or segment.document_id != document_id
        ):
            raise NotFoundException("该文档片段不存在，或无权限修改，请核实后重试")

        # 2.判断文档是否处于可以删除的状态，只有COMPLETED/ERROR才可以删除
        if segment.status not in [SegmentStatus.COMPLETED, SegmentStatus.ERROR]:
            raise FailedException("当前文档片段处于不可删除状态，请稍后尝试")

        # 3.删除文档片段并获取该片段的文档信息
        document = segment.document
        self.delete(segment)

        # 4.同步删除关键词表中属于该片段的关键词
        self.keyword_table_service.delete_keyword_table_from_ids(dataset_id, [segment_id])

        # 5.同步删除向量数据库存储的记录
        try:
            self.vector_database_service.collection.data.delete_by_id(str(segment.node_id))
        except Exception as e:
            logging.exception(f"删除文档片段记录失败, segment_id: {segment_id}, 错误信息: {str(e)}")

        # 6.更新文档信息，涵盖字符总数、token总次数
        document_character_count, document_token_count = self.db.session.query(
            func.coalesce(func.sum(Segment.character_count), 0),
            func.coalesce(func.sum(Segment.token_count), 0)
        ).filter(Segment.document_id == document.id).first()
        self.update(
            document,
            character_count=document_character_count,
            token_count=document_token_count,
        )

        return segment
