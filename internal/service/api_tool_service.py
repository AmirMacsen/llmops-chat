import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from injector import inject
from sqlalchemy import desc

from internal.core.tools.api_tools.entities import OpenAPISchema, ToolEntity
from internal.exception import ValidationException, NotFoundException
from internal.model import ApiTool, ApiToolProvider
from internal.schema.api_tool_schema import CreateOpenAPIToolSchemaRequest, GetApiToolProvidersWithPageRequest, \
    UpdateApiToolProviderRequest
from internal.service.base_service import BaseService
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy
from internal.core.tools.api_tools.providers import ApiProviderManager


@inject
@dataclass
class ApiToolService(BaseService):
    """自定义API插件服务"""
    db: SQLAlchemy # 注入数据库
    api_provider_manager: ApiProviderManager

    @classmethod
    def parse_openapi_schema(cls, openapi_schema_str:str) -> OpenAPISchema:
        """解析传入的openapi_schema字符串"""

        data = json.loads(openapi_schema_str.strip())
        try:
            if not isinstance(data, dict):
                raise
        except:
            raise ValidationException("数据必须符合openapi规范")

        response = OpenAPISchema(**data)
        return response

    def get_api_tool_providers_with_page(self, req:GetApiToolProvidersWithPageRequest)->tuple[list[Any], Paginator]:
        """获取自定义API工具提供者的列表"""
        account_id = "b03d55b5-895e-47c8-b767-6d0015ae60a1"

        # 分页查询器
        paginator = Paginator(db=self.db, req=req)
        # 构建筛选器
        filters = [ApiToolProvider.account_id == account_id]
        if req.search_word.data:
            filters.append(ApiToolProvider.name.ilike(f"%{req.search_word.data}%"))

        # 执行分页并获取数据
        api_tool_providers = paginator.paginate(
            self.db.session.query(ApiToolProvider).filter(*filters).order_by(desc("created_at")),
        )

        return api_tool_providers, paginator

    def update_api_tool_provider(self, provider_id: UUID, req:UpdateApiToolProviderRequest):
        """更新工具提供者的信息"""
        account_id = "b03d55b5-895e-47c8-b767-6d0015ae60a1"

        api_tool_provider = self.get(ApiToolProvider, provider_id)
        if api_tool_provider is None or str(api_tool_provider.account_id) != account_id:
            raise NotFoundException("provider未找到")

        openapi_schema = self.parse_openapi_schema(req.openapi_schema.data)

        # 检测当前账号是否已经创建了同名的工具提供者
        check_api_tool_provider = self.db.session.query(ApiToolProvider).filter(
            ApiToolProvider.account_id == account_id,
            ApiToolProvider.name == req.name.data,
            ApiToolProvider.id != api_tool_provider.id,
        ).one_or_none()
        if check_api_tool_provider:
            raise ValidationException(f"该工具提供者名字{req.name.data}已存在")

        # 删除旧工具
        self.db.session.query(ApiTool).filter(
            ApiTool.provider_id == provider_id,
            ApiTool.account_id == account_id
        ).delete()
        # 修改工具提供者信息
        self.update(
            api_tool_provider,
            name=req.name.data,
            icon=req.icon.data,
            headers=req.headers.data,
            description=openapi_schema.description,
            openapi_schema=req.openapi_schema.data,
        )

        for path, path_item in openapi_schema.paths.items():
            for method, method_item in path_item.items():
                self.create(
                    ApiTool,
                    account_id=account_id,
                    provider_id=api_tool_provider.id,
                    name=method_item.get("operationId"),  # 数据库中的name是传入的operationId
                    description=method_item.get("description"),
                    url=f"{openapi_schema.server}{path}",
                    method=method.upper(),
                    parameters=method_item.get("parameters", [])
                )


    def get_api_tool(self, provider_id: UUID, tool_name:str):
        """根据提供的provider id 和 tool_name 获取工具的详情"""
        account_id = "b03d55b5-895e-47c8-b767-6d0015ae60a1"

        # 获取工具提供者信息
        api_tool = self.db.session.query(ApiTool).filter_by(
            provider_id=provider_id,
            name=tool_name
        ).one_or_none()

        if not api_tool or str(api_tool.account_id) != account_id:
            raise NotFoundException("工具未找到")

        return api_tool

    def get_api_tool_provider(self, provider_id: UUID):
        """通过工具提供者的ID获取提供者的详情"""
        account_id = "b03d55b5-895e-47c8-b767-6d0015ae60a1"

        # 查询数据库获取对应的数据
        api_tool_provider = self.get(ApiToolProvider, provider_id)
        if api_tool_provider is None or str(api_tool_provider.account_id) != account_id:
            raise NotFoundException("provider未找到")
        return api_tool_provider

    def delete_api_tool_provider(self, provider_id: UUID):
        """删除工具提供者和工具的所有信息"""
        account_id = "b03d55b5-895e-47c8-b767-6d0015ae60a1"
        api_tool_provider = self.get(ApiToolProvider, provider_id)
        if api_tool_provider is None or str(api_tool_provider.account_id) != account_id:
            raise NotFoundException("provider未找到")
        with self.db.auto_commit():
            self.db.session.query(ApiTool).filter(
                ApiTool.provider_id == provider_id,
                ApiTool.account_id == account_id
            ).delete()
            self.db.session.delete(api_tool_provider)

    def create_api_tool_provider(self,req:CreateOpenAPIToolSchemaRequest):
        """根据传递的请求信息创建自定义的api 工具"""

        # todo: 授权认证
        account_id = "b03d55b5-895e-47c8-b767-6d0015ae60a1"

        openapi_schema = self.parse_openapi_schema(req.openapi_schema.data)

        # 查询当前登录的账号是否已经创建了同名的工具提供者，如果是则抛出异常
        api_tool_provider = self.db.session.query(ApiToolProvider).filter_by(
            account_id=account_id,
            name=req.name.data
        ).one_or_none()

        if api_tool_provider is not None:
            raise ValidationException(f"当前账号已经创建了同名的插件提供商：{req.name.data}")

        # 开启创建
        api_tool_provider = self.create(
            ApiToolProvider,
            account_id=account_id,
            name=req.name.data,
            icon=req.icon.data,
            description=openapi_schema.description,
            openapi_schema=req.openapi_schema.data,
            headers=req.headers.data
        )

        # 创建api工具
        for path, path_item in openapi_schema.paths.items():
            for method, method_item in path_item.items():
                self.create(
                    ApiTool,
                    account_id=account_id,
                    provider_id=api_tool_provider.id,
                    name=method_item.get("operationId"),  # 数据库中的name是传入的operationId
                    description=method_item.get("description"),
                    url=f"{openapi_schema.server}{path}",
                    method=method.upper(),
                    parameters=method_item.get("parameters",[])
                )


    def api_tool_invoke(self):
        provider_id = "166e64f7-e81a-4f59-af26-9f398cc42ebc"
        tool_name = "YouDaoSuggest"

        api_tool = self.db.session.query(ApiTool).filter(
            ApiTool.provider_id == provider_id,
            ApiTool.name == tool_name,
        ).one_or_none()
        if api_tool is None:
            raise NotFoundException("工具未找到")

        api_tool_provider = api_tool.provider

        tool_entity = ToolEntity(
            id=str(api_tool_provider.id),
            name=api_tool_provider.name,
            url=api_tool.url,
            method=api_tool.method,
            description=api_tool.description,
            headers=api_tool_provider.headers,
            parameters=api_tool.parameters
        )

        tool = self.api_provider_manager.get_tool(tool_entity)
        return tool.invoke({"q": "love", "doctype": "json"})


