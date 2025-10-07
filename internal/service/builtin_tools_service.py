import mimetypes
import os.path
from dataclasses import dataclass
from typing import List, Any
import base64

from flask import current_app
from injector import inject
from pydantic import BaseModel

from internal.core.tools.builtin_tools.categories import BuiltinCategoryManager
from internal.core.tools.builtin_tools.entities import ToolEntity
from internal.core.tools.builtin_tools.providers import BuiltinProviderManager
from internal.exception import NotFoundException


@inject
@dataclass
class BuiltinToolsService:
    """内置工具服务"""

    builtin_provider_manager: BuiltinProviderManager
    builtin_category_manager: BuiltinCategoryManager

    def get_builtin_tools(self) -> List:
        """获取内置插件提供商+工具对应的信息"""
        # 1. 获取所有的提供商
        providers = self.builtin_provider_manager.get_providers()
        # 2.遍历所有的提供商的工具信息
        builtin_tools = []
        for provider in providers:
            # 获取素有的服务商实体
            provider_entity = provider.provider_entity
            builtin_tool = {
                **provider_entity.model_dump(exclude=["icon"]), # 图片单独传递
                "tools": []
            }
            # 获取所有服务商下的工具
            for tool_entity in provider.get_tool_entities():
                tool = provider.get_tool(tool_entity.name)
                tool_dict = {
                    **tool_entity.model_dump(),
                    "inputs": self.get_tool_input(tool)
                }
                builtin_tool["tools"].append(tool_dict)

            builtin_tools.append(builtin_tool)

        return builtin_tools


    def get_provider_tool(self, provider_name:str, tool_name:str):
        """根据服务提供商和工具名称获取指定的工具信息"""
        # 1. 获取内置的提供商
        provider = self.builtin_provider_manager.get_provider(provider_name)
        if provider is None:
            raise NotFoundException(f"未找到提供商: {provider_name}")

        # 2.获取提供商提供的工具
        tool_entity = provider.get_tool_entity(tool_name)
        if tool_entity is None:
            raise NotFoundException(f"未找到工具: {tool_name}")

        # 3.组装提供商和工具实体信息
        provider_entity = provider.provider_entity
        tool = provider.get_tool(tool_entity.name)


        builtin_tool = {
            "provider": {**provider_entity.model_dump(exclude=["icon", "created_at"])},
            **tool_entity.model_dump(),
            "created_at": provider_entity.created_at,
            "inputs": self.get_tool_input(tool)
        }

        return builtin_tool


    def get_provider_icon(self, provider_name:str) -> tuple[bytes, str]:
        """获取提供商的图标"""
        provider = self.builtin_provider_manager.get_provider(provider_name)
        if provider is None:
            raise NotFoundException(f"未找到提供商: {provider_name}")

        # 找到图标的路径信息
        root_path = os.path.dirname(os.path.dirname(current_app.root_path))

        provider_path = os.path.join(
            root_path,
            "internal", "core", "tools", "builtin_tools", "providers", provider_name,
        )

        icon_path = os.path.join(provider_path,"_asset", provider.provider_entity.icon)

        # 检测文件是否存在
        if not os.path.exists(icon_path):
            raise NotFoundException(f"{provider_name} 未找到图标: {provider.provider_entity.icon}")

        # 读取icon类型
        mimetype, _ = mimetypes.guess_type(icon_path)
        mimetype = mimetype or "application/octet-stream"

        # 读取文件
        with open(icon_path, "rb") as f:
            byte_data = f.read()
            return byte_data, mimetype


    def get_categories(self)-> list[dict[str, Any]]:
        """获取所有的分类信息"""
        category_map = self.builtin_category_manager.get_category_map()
        return [{
            "name": category["entity"].name,
            "category": category["entity"].category,
            "icon": base64.b64encode(category["icon"]).decode('utf-8') if isinstance(category["icon"], bytes) else category["icon"]
        } for category in category_map.values()]



    @classmethod
    def get_tool_input(cls, tool:ToolEntity) -> List:
        """根据工具获取input信息"""
        inputs = []
        if hasattr(tool, "args_schema") and issubclass(tool.args_schema, BaseModel):
            inputs = []

            for field_name, model_field in tool.args_schema.model_fields.items():
                # 处理类型注解的序列化
                type_name = None
                if model_field.annotation is not None:
                    if isinstance(model_field.annotation, type):
                        type_name = model_field.annotation.__name__
                    else:
                        # 对于 typing 模块中的类型，如 List[str] 等，返回其字符串表示
                        type_name = str(model_field.annotation).replace('typing.', '')

                inputs.append({
                    "name": field_name,
                    "description": model_field.description or "",
                    "required": model_field.is_required(),
                    "type": type_name
                })

        return inputs