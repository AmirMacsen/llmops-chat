from flask_wtf import FlaskForm
from marshmallow import Schema, fields, pre_dump
from wtforms import StringField, BooleanField
from wtforms.validators import Optional, ValidationError, DataRequired

from internal.lib.helper import datetime_to_timestamp
from internal.model import Segment
from internal.schema import ListField
from pkg.paginator import PaginatorRequest


class GetSegmentWithPageRequest(PaginatorRequest):
    """获取文档片段列表请求"""
    search_word = StringField("search_word", default="",
                              validators=[Optional()])



class GetSegmentWithPageResponse(Schema):
    """获取文档片段响应"""
    id = fields.UUID(dump_default="")
    document_id = fields.UUID(dump_default="")
    dataset_id = fields.UUID(dump_default="")
    position = fields.Integer(dump_default=0)
    content = fields.String(dump_default="")
    keywords = fields.List(fields.String(), dump_default=[])
    character_count = fields.Integer(dump_default=0)
    token_count = fields.Integer(dump_default=0)
    hit_count = fields.Integer(dump_default=0)
    enabled = fields.Boolean(dump_default=True)
    disabled_at = fields.Integer(dump_default=0)
    status = fields.String(dump_default="")
    error = fields.String(dump_default="")
    created_at = fields.Integer(dump_default=0)
    updated_at = fields.Integer(dump_default=0)

    @pre_dump
    def pre_data(self, data:Segment, **kwargs):
        """数据预处理"""
        return {
            "id": str(data.id),
            "document_id": str(data.document_id),
            "dataset_id": str(data.dataset_id),
            "position": data.position,
            "content": data.content,
            "keywords": data.keywords,
            "character_count": data.character_count,
            "token_count": data.token_count,
            "hit_count": data.hit_count,
            "enabled": data.enabled,
            "disabled_at": datetime_to_timestamp(data.disabled_at),
            "status": data.status,
            "error": data.error,
            "created_at": datetime_to_timestamp(data.created_at),
            "updated_at": datetime_to_timestamp(data.updated_at),
        }


class GetSegmentResponse(Schema):
    """获取文档片段响应"""
    id = fields.UUID(dump_default="")
    document_id = fields.UUID(dump_default="")
    dataset_id = fields.UUID(dump_default="")
    position = fields.Integer(dump_default=0)
    content = fields.String(dump_default="")
    keywords = fields.List(fields.String(), dump_default=[])
    character_count = fields.Integer(dump_default=0)
    token_count = fields.Integer(dump_default=0)
    hit_count = fields.Integer(dump_default=0)
    hash = fields.String(dump_default="")
    enabled = fields.Boolean(dump_default=True)
    disabled_at = fields.Integer(dump_default=0)
    status = fields.String(dump_default="")
    error = fields.String(dump_default="")
    created_at = fields.Integer(dump_default=0)
    updated_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data:Segment, **kwargs):
        return {
            "id": str(data.id),
            "document_id": str(data.document_id),
            "dataset_id": str(data.dataset_id),
            "position": data.position,
            "content": data.content,
            "keywords": data.keywords,
            "character_count": data.character_count,
            "token_count": data.token_count,
            "hit_count": data.hit_count,
            "hash": data.hash,
            "enabled": data.enabled,
            "disabled_at": datetime_to_timestamp(data.disabled_at),
            "status": data.status,
            "error": data.error,
            "created_at": datetime_to_timestamp(data.created_at),
            "updated_at": datetime_to_timestamp(data.updated_at),
        }



class UpdateSegmentEnabledRequest(FlaskForm):
    """更新文档片段启用状态请求"""
    enabled = BooleanField("enabled")

    def validate_enabled(self, field: BooleanField) -> None:
        """校验文档启用状态enabled"""
        if not isinstance(field.data, bool):
            raise ValidationError("enabled状态不能为空且必须为布尔值")


class CreateSegmentRequest(FlaskForm):
    """创建文档请求片段结构"""
    content = StringField("content", validators=[
        DataRequired(),
    ])
    keywords = ListField("keywords")

    def validate_keywords(self, field: ListField):
        """校验关键词列表"""
        # 校验数据列表+非空
        if field.data is None:
            field.data = []
        if not isinstance(field.data, list):
            raise ValidationError("keywords数据类型错误")

        # 校验关键词长度，关键词长度不能大于10
        if len(field.data) > 10:
            raise ValidationError("keywords长度不能大于10")

        # 循环校验关键词信息，关键词必须是字符串
        for keyword in field.data:
            if not isinstance(keyword, str):
                raise ValidationError("keywords数据类型错误")

        #   删除重复数据并更新
        field.data = list(dict.fromkeys(field.data))


class UpdateSegmentRequest(FlaskForm):
    """更新文档片段请求"""
    content = StringField("content")
    keywords = ListField("keywords")

    def validate_keywords(self, field: ListField) -> None:
        """校验关键词列表，涵盖长度不能为空，默认为值为空列表"""
        # 1.校验数据类型+非空
        if field.data is None:
            field.data = []
        if not isinstance(field.data, list):
            raise ValidationError("关键词列表格式必须是数组")

        # 2.校验数据的长度，最长不能超过10个关键词
        if len(field.data) > 10:
            raise ValidationError("关键词长度范围数量在1-10")

        # 3.循环校验关键词信息，关键词必须是字符串
        for keyword in field.data:
            if not isinstance(keyword, str):
                raise ValidationError("关键词必须是字符串")

        # 4.删除重复数据并更新
        field.data = list(dict.fromkeys(field.data))