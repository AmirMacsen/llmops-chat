from uuid import UUID

from injector import inject
from dataclasses import dataclass

from internal.entity.cache_entity import LOCK_EXPIRE, LOCK_KEYWORD_TABLE_UPDATE_KEYWORD_TABLE
from internal.model import KeywordTable, Segment
from internal.service.base_service import BaseService
from pkg.sqlalchemy import SQLAlchemy

from redis import Redis


@inject
@dataclass
class KeywordTableService(BaseService):
    """关键词表服务"""
    db: SQLAlchemy
    redis_client: Redis


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


    def delete_keyword_table_from_ids(self, dataset_id: UUID, segment_ids: list[str])->None:
        """根据传入的dataset_id和segment_id删除对应的关键词表"""

        # 删除知识库中关联的关键词表数据，需要上锁，避免并发更新
        cache_key = "LOCK_KEYWORD_TABLE_UPDATE_KEYWORD_TABLE".format(dataset_id)
        with self.redis_client.lock(cache_key, timeout=LOCK_EXPIRE):
            # 获取当前知识库的关键词表
            keyword_table_record = self.get_keyword_table_from_dataset(dataset_id)
            keyword_table = keyword_table_record.keyword_table.copy()

            # 片段id列表转化为集合
            segment_ids_to_delete = set(segment_ids)
            keywords_to_delete = set()
            # 循环遍历关键词表数据
            for keyword, ids in keyword_table.items():
                # 删除该片段id
                ids_set = set(ids)
                if segment_ids_to_delete.intersection(ids_set):
                    keyword_table[keyword] = list(ids_set.difference(segment_ids_to_delete))
                    if not keyword_table[keyword]:
                        keywords_to_delete.add(keyword)

            # 检测空关键词数据并删除
            for keyword in keywords_to_delete:
                del keyword_table[keyword]

            # 确保所有值都是list类型而不是set类型，避免JSON序列化错误
            keyword_table_for_update = {}
            for field, value in keyword_table.items():
                keyword_table_for_update[field] = list(value) if isinstance(value, set) else value

            self.update(keyword_table_record, keyword_table=keyword_table_for_update)


    def add_keyword_table_from_ids(self, dataset_id: UUID, segment_ids: list[str]) -> None:
        """根据传入的dataset_id和片段id"""
        cache_key = LOCK_KEYWORD_TABLE_UPDATE_KEYWORD_TABLE.format(dataset_id)

        with self.redis_client.lock(cache_key, timeout=LOCK_EXPIRE):
            # 获取当前知识库的关键词词表
            keyword_table_record = self.get_keyword_table_from_dataset(dataset_id)

            keyword_table = {
                field: set(value)
                for field, value in keyword_table_record.keyword_table.items()
            }
            # 获取片段关键词
            segments = self.db.session.query(Segment.id, Segment.keywords).filter(
                Segment.dataset_id == dataset_id,
                Segment.id.in_(segment_ids)
            ).all()

            for id, keywords in segments:
                for keyword in keywords:
                    if keyword not in keyword_table:
                        keyword_table[keyword] = set()
                    keyword_table[keyword].add(str(id))

            # 更新关键词表，确保所有值都是list类型而不是set类型
            keyword_table_for_update = {}
            for field, value in keyword_table.items():
                keyword_table_for_update[field] = list(value)

            self.update(
                keyword_table_record,
                keyword_table=keyword_table_for_update
            )