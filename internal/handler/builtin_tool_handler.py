import io

from flask import send_file
from injector import inject
from dataclasses import dataclass
from flask_login import login_required

from internal.service import BuiltinToolsService
from pkg.response import success_json


@inject
@dataclass
class BuiltinToolHandler:
    """内置工具处理"""
    builtin_tool_service: BuiltinToolsService

    @login_required
    def get_builtin_tools(self, **kwargs):
        """
        获取所有内置工具
        ---
        tags:
          - BuiltinTools
        summary: 获取所有内置工具信息
        description: 获取所有内置工具及其提供商信息
        responses:
          200:
            description: 成功获取工具列表
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    code:
                      type: integer
                      example: 200
                    data:
                      type: array
                      items:
                        type: object
        """
        """获取所有内置工具信息+提供商信息"""
        builtin_tools = self.builtin_tool_service.get_builtin_tools()
        print(builtin_tools)
        return success_json(data=builtin_tools)

    @login_required
    def get_provider_tool(self, provider_name:str, tool_name:str):
        """
        获取特定工具信息
        ---
        tags:
          - BuiltinTools
        summary: 根据提供商名称和工具名称获取指定工具信息
        description: 根据传递的提供商名称+工具名称获取指定的工具信息
        parameters:
          - name: provider_name
            in: path
            description: 提供商名称
            required: true
            schema:
              type: string
          - name: tool_name
            in: path
            description: 工具名称
            required: true
            schema:
              type: string
        responses:
          200:
            description: 成功获取工具信息
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    code:
                      type: integer
                      example: 200
                    data:
                      type: object
        """
        """根据传递的提供商名称+工具名称获取指定的工具信息"""
        tools = self.builtin_tool_service.get_provider_tool(provider_name, tool_name)
        return success_json(data=tools)


    @login_required
    def get_provider_icon(self, provider_name:str):
        """
        获取提供商图标
        ---
        tags:
          - BuiltinTools
        summary: 获取服务提供商的图标
        description: 根据提供商名称获取其图标信息
        parameters:
          - name: provider_name
            in: path
            description: 提供商名称
            required: true
            schema:
              type: string
        responses:
          200:
            description: 成功获取图标
            content:
              image/*:
                schema:
                  type: string
                  format: binary
        """
        """获取服务提供商的icon图标信息"""
        icon, mimetype = self.builtin_tool_service.get_provider_icon(provider_name)
        return send_file(io.BytesIO(icon), mimetype)


    @login_required
    def get_categories(self):
        """
        获取所有分类
        ---
        tags:
          - BuiltinTools
        summary: 获取所有内置提供商分类信息
        description: 获取所有内置提供商的分类信息
        responses:
          200:
            description: 成功获取分类信息
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    code:
                      type: integer
                      example: 200
                    data:
                      type: array
                      items:
                        type: object
        """
        """获取所有内置提供商分类信息"""
        category = self.builtin_tool_service.get_categories()
        print(category)
        return success_json(data=category)