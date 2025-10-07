
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