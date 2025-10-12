import logging
import random
import time
from datetime import datetime
from uuid import UUID

from injector import inject
from dataclasses import dataclass

from redis import Redis
from sqlalchemy import desc, asc, func

from internal.entity.cache_entity import LOCK_DOCUMENT_UPDATE_ENABLED, LOCK_EXPIRE
from internal.entity.dataset_entity import DocumentProcessType, SegmentStatus, DocumentStatus
from internal.entity.upload_file_entity import ALLOW_FILE_EXTENSIONS
from internal.lib.helper import datetime_to_timestamp
from internal.model import Document, Dataset, UploadFile, ProcessRule, Segment
from internal.schema.document_schema import GetDocumentsWithPageRequest
from internal.service.base_service import BaseService
from internal.task import document_task
from internal.task.document_task import update_document_enabled, delete_document
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy
from internal.exception import NotFoundException, ForbiddenException, FailedException


@inject
@dataclass
class DocumentService(BaseService):
    """文档服务"""
    db: SQLAlchemy
    redis_client: Redis

    def create_document(self, dataset_id: UUID,
                        upload_file_ids: list[UUID],
                        process_type: str = DocumentProcessType.AUTOMIC,
                        rule: dict = None
                        ) -> tuple[list[Document], str]:
        """根据传入的文档列表异步处理"""
        account_id = "b03d55b5-895e-47c8-b767-6d0015ae60a1"

        dataset = self.get(Dataset, dataset_id)
        if not dataset or str(dataset.account_id) != account_id:
            raise ForbiddenException("知识库不存在")

        # 提取文件并校验文件权限与文件扩展
        upload_files = self.db.session.query(UploadFile).filter(
            UploadFile.account_id == account_id,
            UploadFile.id.in_(upload_file_ids)
        ).all()

        upload_files = [upload_file for upload_file in upload_files
                        if upload_file.extension.lower() in ALLOW_FILE_EXTENSIONS]
        if len(upload_files) == 0:
            logging.warning(
                f"上传文档列表未解析到合法文件，account_id: {account_id}, dataset_id: {dataset_id}, upload_file_ids: {upload_file_ids}"
            )
            raise FailedException("没有有效文件")

        # 创建批次和处理规则并记录到数据库中
        batch = time.strftime("%Y%m%d%H%M%S" + str(random.randint(100000, 999999)))
        process_rule = self.create(
            ProcessRule,
            account_id=account_id,
            dataset_id=dataset_id,
            mode=process_type,
            rule=rule
        )

        # 获取当前知识库的最新文档位置
        position = self.get_document_position(dataset_id)

        # 循环遍历所有合法的文件列表并记录
        documents = []
        for upload_file in upload_files:
            position += 1
            document = self.create(
                Document,
                account_id=account_id,
                dataset_id=dataset_id,
                upload_file_id=upload_file.id,
                process_rule_id=process_rule.id,
                position=position,
                batch=batch,
                name=upload_file.name
            )
            documents.append(document)

        # 调用异步任务执行后续操作
        document_task.build_document.delay([doc.id for doc in documents])

        # 返回文档列表和处理批次
        return documents, batch

    def get_documents_status(self, dataset_id: UUID, batch: str) -> list[dict]:
        """获取文档处理状态"""
        account_id = "b03d55b5-895e-47c8-b767-6d0015ae60a1"

        # 权限检测
        dataset = self.get(Dataset, dataset_id)
        if not dataset or str(dataset.account_id) != account_id:
            raise ForbiddenException("知识库不存在")

        # 查询知识库下的文档列表
        documents = self.db.session.query(Document).filter(
            Document.dataset_id == dataset_id,
            Document.batch == batch
        ).order_by(asc("position")).all()

        if not documents or len(documents) == 0:
            raise NotFoundException("没有文档")

        # 提取状态数据
        documents_status = []
        for document in documents:
            upload_file = document.upload_file
            # 查询每个文档的总片段数量和已经构建完成的片段数量
            segment_count = self.db.session.query(
                func.count(Segment.id)
            ).filter(
                Segment.document_id == document.id
            ).scalar()

            completed_segment_count = self.db.session.query(
                func.count(Segment.id)
            ).filter(
                Segment.document_id == document.id,
                Segment.status == SegmentStatus.COMPLETED
            ).scalar()

            documents_status.append({
                "id": str(document.id),
                "name": document.name,
                "size": upload_file.size,
                "extension": upload_file.extension,
                "mime_type": upload_file.mime_type,
                "status": document.status,
                "position": document.position,
                "segment_count": segment_count,
                "completed_segment_count": completed_segment_count,
                "error": document.error,
                "processing_started_at": datetime_to_timestamp(document.processing_started_at),
                "parsing_completed_at": datetime_to_timestamp(document.parsing_completed_at),
                "splitting_completed_at": datetime_to_timestamp(document.splitting_completed_at),
                "indexing_completed_at": datetime_to_timestamp(document.indexing_completed_at),
                "completed_at": datetime_to_timestamp(document.completed_at),
                "stopped_at": datetime_to_timestamp(document.stopped_at),
                "created_at": datetime_to_timestamp(document.created_at),
            })

        return documents_status

    def get_document(self, dataset_id: UUID, document_id: UUID) -> Document:
        """获取文档信息"""
        account_id = "b03d55b5-895e-47c8-b767-6d0015ae60a1"
        # 权限检测
        dataset = self.get(Dataset, dataset_id)
        if not dataset or str(dataset.account_id) != account_id:
            raise ForbiddenException("知识库不存在")

        document = self.get(Document, document_id)
        if document is None:
            raise NotFoundException("文档不存在")

        if document.dataset_id != dataset_id or str(document.account_id) != account_id:
            raise ForbiddenException("文档不属于该知识库")
        return document

    def get_documents_with_page(self, dataset_id: UUID, req: GetDocumentsWithPageRequest) -> tuple[
        list[Document], Paginator]:
        """根据传递的知识库ID获取分页数据"""
        account_id = "b03d55b5-895e-47c8-b767-6d0015ae60a1"
        # 权限检测
        dataset = self.get(Dataset, dataset_id)
        if not dataset or str(dataset.account_id) != account_id:
            raise ForbiddenException("知识库不存在")

        paginator = Paginator(db=self.db, req=req)

        # 构建筛选器
        filters = [
            Document.dataset_id == dataset_id,
            Document.account_id == account_id
        ]

        if req.search_word.data:
            filters.append(Document.name.ilike(f"%{req.search_word.data}%"))

        documents = paginator.paginate(
            self.db.session.query(Document).filter(*filters).order_by(desc("created_at"))
        )
        return documents, paginator

    def update_document(self, dataset_id: UUID, document_id: UUID, **kwargs) -> Document:
        """更新文档名称"""
        account_id = "b03d55b5-895e-47c8-b767-6d0015ae60a1"
        # 权限检测
        dataset = self.get(Dataset, dataset_id)
        if not dataset or str(dataset.account_id) != account_id:
            raise ForbiddenException("知识库不存在")

        document = self.get(Document, document_id)
        if document is None:
            raise NotFoundException("文档不存在")

        if document.dataset_id != dataset_id or str(document.account_id) != account_id:
            raise ForbiddenException("文档不属于该知识库")

        return self.update(document, **kwargs)

    def update_document_enabled(self, dataset_id: UUID, document_id: UUID, enabled: bool) -> Document:
        """更新文档启用状态"""
        account_id = "b03d55b5-895e-47c8-b767-6d0015ae60a1"
        # 权限检测
        dataset = self.get(Dataset, dataset_id)
        if not dataset or str(dataset.account_id) != account_id:
            raise ForbiddenException("知识库不存在")

        # 获取文档并校验权限
        document = self.get(Document, document_id)
        if document is None:
            raise NotFoundException("文档不存在")

        if document.dataset_id != dataset_id or str(document.account_id) != account_id:
            raise ForbiddenException("文档不属于该知识库")

        # 判断文档是否属于可以修改的状态，只有构建完成才能修改
        if document.status != DocumentStatus.COMPLETED:
            raise ForbiddenException("文档正在处理中，暂时无法修改")

        # 判断当前的文档的启用状态是否与当前传递的启用状态相反（如果相同，没必要处理，太废资源）
        if document.enabled == enabled:
            raise ForbiddenException(f"文档已处于该状态 {'启用' if enabled else '禁用'}")

        # 构建缓存锁名字，并检测是否上锁
        cache_key = LOCK_DOCUMENT_UPDATE_ENABLED.format(document_id=document_id)
        cache_result = self.redis_client.get(cache_key)
        if cache_result:
            raise ForbiddenException("文档正在处理中，请稍后再试")

        # 修改文档的启用状态并设置缓存锁
        self.update(document, enabled=enabled, disabled_at=datetime.now() if not enabled else None)
        self.redis_client.setex(cache_key, LOCK_EXPIRE, 1)

        # 启用异步任务完成后续操作
        update_document_enabled.delay(document.id)
        return document


    def delete_document(self, dataset_id: UUID, document_id: UUID) -> Document:
        """删除文档 【文档、片段删除、词表更新、weaviate向量删除】"""
        account_id = "b03d55b5-895e-47c8-b767-6d0015ae60a1"
        # 权限检测
        dataset = self.get(Dataset, dataset_id)
        if not dataset or str(dataset.account_id) != account_id:
            raise ForbiddenException("知识库不存在")

        # 获取文档并校验权限
        document = self.get(Document, document_id)
        if document is None:
            raise NotFoundException("文档不存在")

        if document.dataset_id != dataset_id or str(document.account_id) != account_id:
            raise ForbiddenException("文档不属于该知识库")

        # 已经构建完成或者发生错误的文档才可以删除
        if document.status not in [DocumentStatus.COMPLETED, DocumentStatus.ERROR]:
            raise ForbiddenException("文档正在处理中，请稍后再试")

        # 删除pg中的文档
        self.delete(document)

        # 调用异步任务执行后续操作，涵盖删除片段、更新词表、删除向量
        delete_document.delay(dataset_id, document_id)
        return document


    def get_document_position(self, dataset_id: UUID) -> int:
        """获取当前知识库的最新文档位置"""
        document = self.db.session.query(Document).filter(
            Document.dataset_id == dataset_id
        ).order_by(desc("position")).first()
        return document.position if document else 0
