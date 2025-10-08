from injector import provider
from marshmallow import Schema, fields, pre_dump
from flask_wtf import FlaskForm
from wtforms.fields.simple import StringField
from wtforms.validators import DataRequired, Length, URL, Optional

from internal.model import ApiToolProvider, ApiTool
from internal.exception import ValidationException
from internal.schema import ListField
from pkg.paginator import PaginatorRequest


class ValidateOpenAPISchemaRequest(FlaskForm):
    """校验OpenAPI规范字符串请求"""
    openapi_schema = StringField("openapi_schema", validators=[
        DataRequired(message="请输入OpenAPI规范字符串")
    ])

class GetApiToolProvidersWithPageRequest(PaginatorRequest):
    """获取API工具提供商列表请求"""
    search_word = StringField("search_word", validators=[
        Optional()
    ])

class UpdateApiToolProviderRequest(FlaskForm):
    """更新API工具提供商请求"""
    name = StringField("name", validators=[
        DataRequired(message="请输入工具名称"),
        Length(min=1, max=30, message="工具名称长度必须在1-30个字符之间")
    ])
    icon = StringField("name", validators=[
        DataRequired(message="请填入工具提供者的图标"),
        URL(message="工具提供者的icon必须是url链接")
    ])

    openapi_schema = StringField("openapi_schema", validators=[
        DataRequired(message="请输入OpenAPI规范字符串")
    ])

    headers = ListField("headers", default=[])

    @classmethod
    def validate_headers(cls, form, field):
        """验证headers字段"""
        for header in field.data:
            if not isinstance(header, dict):
                raise ValidationException("headers字段必须是字典")

            if set(header.keys()) != {"key", "value"}:
                raise ValidationException("headers字段的key必须是key和value")

class GetApiToolProvidersWithPageResponse(Schema):
    """获取API工具提供商列表响应"""
    id = fields.UUID(description="服务提供商ID")
    name = fields.Str(description="提供商名称")
    icon = fields.Str(description="提供商图标")
    description = fields.Str(description="提供商描述")
    headers = fields.List(fields.Dict, default={}, description="请求头")
    tools = fields.List(fields.Dict, default={}, description="工具列表")
    created_at = fields.Int(default=0, description="创建时间")

    @pre_dump
    def process_data(self, data:ApiToolProvider, **kwargs):
        tools = data.tools # 写出来只会执行一次，否则取一次执行一次
        return {
            "id": data.id,
            "name": data.name,
            "icon": data.icon,
            "description": data.description,
            "headers": data.headers,
            "tools": [{
                "id": tool.id,
                "description":data.description,
                "name": tool.name,
                "inputs": [{k:v for k,v in params.items() if k != "in"} for params in tool.parameters]
            } for tool in data.tools],
            "created_at": int(data.created_at.timestamp())
        }


class CreateOpenAPIToolSchemaRequest(FlaskForm):
    """创建OpenAPI工具请求"""
    name = StringField("name", validators=[
        DataRequired(message="请输入工具名称"),
        Length(min=1, max=30, message="工具名称长度必须在1-30个字符之间")
    ])
    icon = StringField("name", validators=[
        DataRequired(message="请填入工具提供者的图标"),
        URL(message="工具提供者的icon必须是url链接")
    ])

    openapi_schema = StringField("openapi_schema", validators=[
        DataRequired(message="请输入OpenAPI规范字符串")
    ])

    headers = ListField("headers", default=[])

    @classmethod
    def validate_headers(cls, form, field):
        """验证headers字段"""
        for header in field.data:
            if not isinstance(header, dict):
                raise ValidationException("headers字段必须是字典")

            if set(header.keys()) != {"key", "value"}:
                raise ValidationException("headers字段的key必须是key和value")


class GetApiToolProviderResponse(Schema):
    """获取API工具提供商响应"""
    id = fields.UUID(description="服务提供商ID")
    name = fields.Str(description="提供商名称")
    icon = fields.Str(description="提供商图标")
    openapi_schema = fields.Str(description="OpenAPI规范")
    headers = fields.List(fields.Dict(),default=[], description="请求头")
    created_at = fields.Int(default=0, description="创建时间")

    @pre_dump
    def process_data(self, data:ApiToolProvider, **kwargs):
        return {
            "id": data.id,
            "name": data.name,
            "icon": data.icon,
            "openapi_schema": data.openapi_schema,
            "headers": data.headers,
            "created_at": int(data.created_at.timestamp())
        }


class GetApiToolResponse(Schema):
    """获取API工具参数详情"""
    id = fields.UUID(description="工具ID")
    name = fields.Str(description="工具名称")
    description = fields.Str(description="工具描述")
    inputs = fields.List(fields.Dict(), default=[], description="工具参数")
    provider = fields.Dict(description="工具提供者信息")

    @pre_dump
    def process_data(self, data:ApiTool, **kwargs):
        provider_info = data.provider
        return {
            "id": data.id,
            "name": data.name,
            "description": data.description,
            "inputs": [{k:v for k,v in params.items() if k != "in"} for params in data.parameters],
            "provider": {
                "id": provider_info.id,
                "name": provider_info.name,
                "icon": provider_info.icon,
                "description": provider_info.description,
                "headers": provider_info.headers,
            }
        }
