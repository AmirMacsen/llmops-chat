import io

from flask import send_file
from injector import inject
from dataclasses import dataclass

from internal.service import BuiltinToolsService
from pkg.response import success_json


@inject
@dataclass
class BuiltinToolHandler:
    """内置工具处理"""
    builtin_tool_service: BuiltinToolsService

    def get_builtin_tools(self, **kwargs):
        """获取所有内置工具信息+提供商信息"""
        builtin_tools = self.builtin_tool_service.get_builtin_tools()
        print(builtin_tools)
        return success_json(data=builtin_tools)

    def get_provider_tool(self, provider_name:str, tool_name:str):
        """根据传递的提供商名称+工具名称获取指定的工具信息"""
        tools = self.builtin_tool_service.get_provider_tool(provider_name, tool_name)
        return success_json(data=tools)


    def get_provider_icon(self, provider_name:str):
        """获取服务提供商的icon图标信息"""
        icon, mimetype = self.builtin_tool_service.get_provider_icon(provider_name)
        return send_file(io.BytesIO(icon), mimetype)


    def get_categories(self):
        """获取所有内置提供商分类信息"""
        category = self.builtin_tool_service.get_categories()
        print(category)
        return success_json(data=category)