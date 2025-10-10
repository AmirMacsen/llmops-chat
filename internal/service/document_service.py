import logging
import random
import time
from uuid import UUID

from injector import inject
from dataclasses import dataclass

from sqlalchemy import desc

from internal.entity.dataset_entity import DocumentProcessType
from internal.entity.upload_file_entity import ALLOW_FILE_EXTENSIONS
from internal.model import Document, Dataset, UploadFile, ProcessRule
from internal.service.base_service import BaseService
from internal.task import document_task
from pkg.sqlalchemy import SQLAlchemy
from internal.exception import NotFoundException,ForbiddenException,FailedException


@inject
@dataclass
class DocumentService(BaseService):
    """文档服务"""
    db: SQLAlchemy

    def create_document(self, dataset_id:UUID,
                        upload_file_ids:list[UUID],
                        process_type:str=DocumentProcessType.AUTOMIC,
                        rule:dict=None
                        ) ->tuple[list[Document], str]:
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
        if len(upload_files)==0:
            logging.warning(
                f"上传文档列表未解析到合法文件，account_id: {account_id}, dataset_id: {dataset_id}, upload_file_ids: {upload_file_ids}"
            )
            raise FailedException("没有有效文件")

        # 创建批次和处理规则并记录到数据库中
        batch = time.strftime("%Y%m%d%H%M%S"+str(random.randint(100000, 999999)))
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


    def get_document_position(self, dataset_id:UUID) -> int:
        """获取当前知识库的最新文档位置"""
        document = self.db.session.query(Document).filter(
            Document.dataset_id == dataset_id
        ).order_by(desc("position")).first()
        return document.position if document else 0





