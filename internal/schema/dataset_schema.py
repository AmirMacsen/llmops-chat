from flask_wtf import FlaskForm
from marshmallow import Schema, fields, pre_dump
from wtforms import StringField
from wtforms.fields.numeric import IntegerField, FloatField
from wtforms.validators import DataRequired, Length, URL, Optional, AnyOf, NumberRange

from internal.entity.dataset_entity import RetrievalStrategy
from internal.lib.helper import datetime_to_timestamp
from internal.model import Dataset
from pkg.paginator import PaginatorRequest


class CreateDatasetRequest(FlaskForm):
    """创建知识库请求"""
    name = StringField('name', validators=[
        DataRequired('知识库名称不能为空'), Length(max=100, message='知识库名称长度不能超过100个字符')
    ])
    icon = StringField('icon', validators=[
        DataRequired('图标不能为空'),
        URL(message="icon必须是URL地址")
    ])
    description = StringField('description', default="", validators=[
        Optional(),
        Length(max=2000, message='描述长度不能超过2000个字符')
    ])



class GetDatasetResponse(Schema):
    """获取知识库详情响应结构"""
    id = fields.UUID(dump_default="")
    name = fields.String(dump_default="")
    icon = fields.String(dump_default="")
    description = fields.String(dump_default="")
    document_count = fields.Integer(dump_default=0)
    hit_count = fields.Integer(dump_default=0)
    related_app_count = fields.Integer(dump_default=0)
    character_count = fields.Integer(dump_default=0)
    updated_at = fields.Integer(dump_default=0)
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: Dataset, **kwargs):
        return {
            "id": data.id,
            "name": data.name,
            "icon": data.icon,
            "description": data.description,
            "document_count": data.document_count,
            "hit_count": data.hit_count,
            "related_app_count": data.related_app_count,
            "character_count": data.character_count,
            "updated_at": int(data.updated_at.timestamp()),
            "created_at": int(data.created_at.timestamp()),
        }


class UpdateDatasetRequest(FlaskForm):
    """更新知识库请求"""
    name = StringField("name", validators=[
        DataRequired("知识库名称不能为空"),
        Length(max=100, message="知识库名称长度不能超过100字符"),
    ])
    icon = StringField("icon", validators=[
        DataRequired("知识库图标不能为空"),
        URL(message="知识库图标必须是图片URL地址"),
    ])
    description = StringField("description", default="", validators=[
        Optional(),
        Length(max=2000, message="知识库描述长度不能超过2000字符")
    ])


class GetDatasetsWithPageRequest(PaginatorRequest):
    """获取知识库分页列表请求数据"""
    search_word = StringField("search_word", default="", validators=[
        Optional(),
    ])


class GetDatasetsWithPageResponse(Schema):
    """获取知识库分页列表响应数据"""
    id = fields.UUID(dump_default="")
    name = fields.String(dump_default="")
    icon = fields.String(dump_default="")
    description = fields.String(dump_default="")
    document_count = fields.Integer(dump_default=0)
    related_app_count = fields.Integer(dump_default=0)
    character_count = fields.Integer(dump_default=0)
    updated_at = fields.Integer(dump_default=0)
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: Dataset, **kwargs):
        return {
            "id": data.id,
            "name": data.name,
            "icon": data.icon,
            "description": data.description,
            "document_count": data.document_count,
            "related_app_count": data.related_app_count,
            "character_count": data.character_count,
            "updated_at": int(data.updated_at.timestamp()),
            "created_at": int(data.created_at.timestamp()),
        }


class HitRequest(FlaskForm):
    """文档召回请求"""
    query = StringField("query", validators=[
        DataRequired("query不能为空"),
        Length(max=200, message="query长度不能超过200字符")
    ])

    retrieval_strategy = StringField("retrieval_strategy", validators=[
        DataRequired("retrieval_strategy不能为空"),
        AnyOf([item.value for item in RetrievalStrategy], message="retrieval_strategy参数错误")
    ])
    k = IntegerField("k", validators=[
        DataRequired("k不能为空"),
        NumberRange(min=1, max=10, message="最大召回数量1-10")
    ])
    score = FloatField("score", validators=[
        NumberRange(min=0, max=1, message="score参数错误")
    ])


class GetDatasetQueriesResponse(Schema):
    """获取知识库查询记录响应数据"""
    id = fields.UUID(dump_default="")
    dataset_id = fields.UUID(dump_default="")
    query = fields.String(dump_default="")
    source = fields.String(dump_default="")
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: Dataset, **kwargs):
        return {
            "id": data.id,
            "dataset_id": data.dataset_id,
            "query": data.query,
            "source": data.source,
            "created_at": datetime_to_timestamp(data.created_at),
        }