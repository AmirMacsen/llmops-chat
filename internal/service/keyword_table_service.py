from uuid import UUID

from injector import inject
from dataclasses import dataclass

from internal.model import KeywordTable
from internal.service.base_service import BaseService
from pkg.sqlalchemy import SQLAlchemy


@inject
@dataclass
class KeywordTableService(BaseService):
    """关键词表服务"""
    db: SQLAlchemy

    def get_keyword_table_from_dataset(self, dataset_id:UUID) -> KeywordTable:
        """根据传入的dataset_id查询其下的关键词词表"""
        keyword_table = self.db.session.query(KeywordTable).filter(
            KeywordTable.dataset_id == dataset_id
        ).one_or_none()
        if not keyword_table:
            keyword_table = self.create(
                KeywordTable,
                dataset_id=dataset_id,
                keyword_table = {}
            )

        return keyword_table
