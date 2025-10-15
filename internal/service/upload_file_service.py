from injector import inject
from dataclasses import dataclass

from internal.model import UploadFile, Account
from internal.service.base_service import BaseService
from pkg.sqlalchemy import SQLAlchemy


@inject
@dataclass
class UploadFileService(BaseService):
    """上传文件服务"""
    db: SQLAlchemy

    def create_upload_file(self, account: Account = None, **kwargs) -> UploadFile:
        """创建上传文件"""
        account_id = str(account.id) if account else "b03d55b5-895e-47c8-b767-6d0015ae60a1"
            
        return self.create(UploadFile, account_id=account_id, **kwargs)