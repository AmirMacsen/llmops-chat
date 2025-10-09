from injector import inject
from dataclasses import dataclass

from internal.model import UploadFile
from internal.service.base_service import BaseService
from pkg.sqlalchemy import SQLAlchemy


@inject
@dataclass
class UploadFileService(BaseService):
    """上传文件服务"""
    db: SQLAlchemy

    def create_upload_file(self, **kwargs) -> UploadFile:
        """创建上传文件"""
        return self.create(UploadFile, **kwargs)