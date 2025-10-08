from dataclasses import dataclass
from uuid import UUID

from injector import inject
from flask import request

from internal.schema.api_tool_schema import ValidateOpenAPISchemaRequest, CreateOpenAPIToolSchemaRequest, \
    GetApiToolProviderResponse, GetApiToolResponse, GetApiToolProvidersWithPageRequest, \
    GetApiToolProvidersWithPageResponse, UpdateApiToolProviderRequest
from internal.service import ApiToolService
from pkg.response import validate_error_json, success_json
from pkg.paginator import PageModel


@inject
@dataclass
class ApiToolHandler:
    """自定义API插件处理器"""
    api_tool_service: ApiToolService

    def get_api_tool_providers_with_page(self):
        """
        获取API工具提供者列表信息，支持分页和搜索
        ---
        tags:
          - ApiTools
        summary: 获取API工具提供者列表
        description: 获取API工具提供者列表信息，该接口支持分页和搜索功能
        parameters:
          - name: page
            in: query
            required: false
            schema:
              type: integer
              example: 1
            description: 页码
          - name: limit
            in: query
            required: false
            schema:
              type: integer
              example: 10
            description: 每页数量
          - name: search_word
            in: query
            required: false
            schema:
              type: string
            description: 搜索关键词
        responses:
          200:
            description: 成功获取API工具提供者列表
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    code:
                      type: string
                      example: "success"
                    data:
                      type: object
                      properties:
                        items:
                          type: array
                          items:
                            type: object
                            properties:
                              id:
                                type: string
                                format: uuid
                                description: 服务提供商ID
                              name:
                                type: string
                                description: 提供商名称
                              icon:
                                type: string
                                description: 提供商图标
                              description:
                                type: string
                                description: 提供商描述
                              headers:
                                type: array
                                description: 请求头
                                items:
                                  type: object
                              tools:
                                type: array
                                description: 工具列表
                                items:
                                  type: object
                              created_at:
                                type: integer
                                description: 创建时间戳
                        paginator:
                          type: object
                          properties:
                            page:
                              type: integer
                              example: 1
                            limit:
                              type: integer
                              example: 10
                            total:
                              type: integer
                              example: 20
                            has_prev:
                              type: boolean
                              example: false
                            has_next:
                              type: boolean
                              example: true
          400:
            description: 请求参数错误
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    code:
                      type: string
                      example: "validate_error"
                    message:
                      type: string
                      example: "参数验证失败"
                    data:
                      type: object
        """
        req = GetApiToolProvidersWithPageRequest(request.args)
        if not req.validate():
            return validate_error_json(req.errors)
        api_tool_providers, paginator = self.api_tool_service.get_api_tool_providers_with_page(req)

        resp = GetApiToolProvidersWithPageResponse(many=True)
        return success_json(data=PageModel(resp.dump(api_tool_providers), paginator=paginator))


    def update_api_tool_provider(self, provider_id: UUID):
        """
        更新自定义API工具提供者信息
        ---
        tags:
          - ApiTools
        summary: 更新API工具提供者
        description: 根据提供者ID更新自定义API工具提供者信息
        parameters:
          - name: provider_id
            in: path
            required: true
            schema:
              type: string
              format: uuid
            description: 工具提供者ID
        requestBody:
          content:
            application/json:
              schema:
                type: object
                required:
                  - name
                  - icon
                  - openapi_schema
                properties:
                  name:
                    type: string
                    description: 工具名称
                    example: "自定义工具1"
                  icon:
                    type: string
                    description: 工具图标URL
                    example: "https://cdn.nlark.com/yuque/0/2025/svg/25668184/1759841318161-9e28f467-02f1-4dc7-9845-3c7dda354e61.svg"
                  openapi_schema:
                    type: string
                    description: OpenAPI规范字符串
                    example: '{"server":"http://baidu.com","description":"baidu","paths":{"/location":{"get":{"description":"获取位置信息","operationId":"xxxx","parameters":[{"name":"location","description":"位置信息","in":"query","required":true,"type":"str"}]}}}}'
                  headers:
                    type: array
                    description: 请求头信息
                    items:
                      type: object
                      properties:
                        key:
                          type: string
                        value:
                          type: string
                    example: [{"key": "Authorization", "value": "Bearer access_token"}]
        responses:
          200:
            description: 更新成功
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    code:
                      type: string
                      example: "success"
                    data:
                      type: string
                      example: "更新成功"
          400:
            description: 请求参数错误
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    code:
                      type: string
                      example: "validate_error"
                    message:
                      type: string
                      example: "参数验证失败"
                    data:
                      type: object
          404:
            description: 提供者未找到
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    code:
                      type: string
                      example: "not_found"
                    message:
                      type: string
                      example: "provider未找到"
                    data:
                      type: object
        """
        req = UpdateApiToolProviderRequest()
        if not req.validate():
            return validate_error_json(req.errors)
        self.api_tool_service.update_api_tool_provider(provider_id, req)

        return success_json(data="更新成功")



    def create_open_api_tool_provider(self):
        """
        创建OpenAI工具
        ---
        tags:
          - ApiTools
        summary: 创建OpenAI工具
        description: 根据提供的OpenAPI规范创建自定义API工具
        requestBody:
          content:
            application/json:
              schema:
                type: object
                required:
                  - name
                  - icon
                  - openapi_schema
                properties:
                  name:
                    type: string
                    description: 工具名称
                    example: "自定义工具1"
                  icon:
                    type: string
                    description: 工具图标URL
                    example: "https://cdn.nlark.com/yuque/0/2025/svg/25668184/1759841318161-9e28f467-02f1-4dc7-9845-3c7dda354e61.svg"
                  openapi_schema:
                    type: string
                    description: OpenAPI规范字符串
                    example: '{"server":"http://baidu.com","description":"baidu","paths":{"/location":{"get":{"description":"获取位置信息","operationId":"xxxx","parameters":[{"name":"location","description":"位置信息","in":"query","required":true,"type":"str"}]}}}}'
                  headers:
                    type: array
                    description: 请求头信息
                    items:
                      type: object
                      properties:
                        key:
                          type: string
                        value:
                          type: string
                    example: [{"key": "Authorization", "value": "Bearer access_token"}]
        responses:
          200:
            description: 创建成功
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    code:
                      type: string
                      example: "success"
                    data:
                      type: string
                      example: "创建自定义插件成功"
          400:
            description: 请求参数错误
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    code:
                      type: string
                      example: "validate_error"
                    message:
                      type: string
                      example: "参数验证失败"
                    data:
                      type: object
        """
        # 提取api请求的数据并校验
        req = CreateOpenAPIToolSchemaRequest()
        if not req.validate():
            return validate_error_json(req.errors)

        # 调用服务创建API工具
        self.api_tool_service.create_api_tool_provider(req)
        return success_json(data="创建自定义插件成功")



    def get_api_tool(self, provider_id: UUID, tool_name:str):
        """
        获取指定工具详情
        ---
        tags:
          - ApiTools
        summary: 获取API工具详情
        description: 根据provider_id和tool_name获取特定API工具的详细信息
        parameters:
          - name: provider_id
            in: path
            required: true
            schema:
              type: string
              format: uuid
            description: 工具提供者ID
          - name: tool_name
            in: path
            required: true
            schema:
              type: string
            description: 工具名称
        responses:
          200:
            description: 成功获取工具详情
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    code:
                      type: string
                      example: "success"
                    data:
                      type: object
                      properties:
                        id:
                          type: string
                          format: uuid
                          description: 工具ID
                        name:
                          type: string
                          description: 工具名称
                        description:
                          type: string
                          description: 工具描述
                        inputs:
                          type: array
                          description: 工具参数列表
                          items:
                            type: object
                        provider:
                          type: object
                          description: 工具提供者信息
                          properties:
                            id:
                              type: string
                              format: uuid
                            name:
                              type: string
                            icon:
                              type: string
                            description:
                              type: string
                            headers:
                              type: array
                              items:
                                type: object
          404:
            description: 工具未找到
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    code:
                      type: string
                      example: "not_found"
                    message:
                      type: string
                      example: "工具未找到"
                    data:
                      type: object
        """
        api_tool = self.api_tool_service.get_api_tool(provider_id, tool_name)
        resp = GetApiToolResponse()
        return success_json(resp.dump(api_tool))



    def get_api_tool_provider(self, provider_id: UUID):
        """
        获取工具提供者详情
        ---
        tags:
          - ApiTools
        summary: 获取API工具提供者详情
        description: 通过工具提供者的ID获取提供者的详细信息
        parameters:
          - name: provider_id
            in: path
            required: true
            schema:
              type: string
              format: uuid
            description: 工具提供者ID
        responses:
          200:
            description: 成功获取工具提供者详情
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    code:
                      type: string
                      example: "success"
                    data:
                      type: object
                      properties:
                        id:
                          type: string
                          format: uuid
                          description: 服务提供商ID
                        name:
                          type: string
                          description: 提供商名称
                        icon:
                          type: string
                          description: 提供商图标
                        openapi_schema:
                          type: string
                          description: OpenAPI规范
                        headers:
                          type: array
                          description: 请求头
                          items:
                            type: object
                        created_at:
                          type: integer
                          description: 创建时间戳
          404:
            description: 提供者未找到
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    code:
                      type: string
                      example: "not_found"
                    message:
                      type: string
                      example: "provider未找到"
                    data:
                      type: object
        """
        api_tool_provider = self.api_tool_service.get_api_tool_provider(provider_id)
        resp = GetApiToolProviderResponse()
        return success_json(resp.dump(api_tool_provider))


    def delete_api_tool_provider(self, provider_id: UUID):
        """
        删除API工具提供者
        ---
        tags:
          - ApiTools
        summary: 删除API工具提供者
        description: 删除指定的API工具提供者及其相关的所有工具
        parameters:
          - name: provider_id
            in: path
            required: true
            schema:
              type: string
              format: uuid
            description: 工具提供者ID
        responses:
          200:
            description: 删除成功
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    code:
                      type: string
                      example: "success"
                    data:
                      type: string
                      example: "删除成功"
          404:
            description: 提供者未找到
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    code:
                      type: string
                      example: "not_found"
                    message:
                      type: string
                      example: "provider未找到"
                    data:
                      type: object
        """
        self.api_tool_service.delete_api_tool_provider(provider_id)
        return success_json(data="删除成功")

    def validate_open_ai_schema(self):
        """
        验证OpenAPI规范
        ---
        tags:
          - ApiTools
        summary: 验证OpenAPI规范格式
        description: 验证前端传入的OpenAPI规范格式是否正确
        requestBody:
          content:
            application/json:
              schema:
                type: object
                required:
                  - openapi_schema
                properties:
                  openapi_schema:
                    type: string
                    description: OpenAPI规范字符串
                    example: '{"server":"http://baidu.com","description":"baidu","paths":{"/location":{"get":{"description":"获取位置信息","operationId":"xxxx","parameters":[{"name":"location","description":"位置信息","in":"query","required":true,"type":"str"}]}}}}'
        responses:
          200:
            description: 成功验证OpenAPI规范
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    code:
                      type: string
                      example: "success"
                    data:
                      type: object
          400:
            description: 请求参数错误
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    code:
                      type: string
                      example: "validate_error"
                    message:
                      type: string
                      example: "参数验证失败"
                    data:
                      type: object
        """
        # 校验前端传入的工具参数描述是否正确
        # 1. 提取前端的数据并进行校验
        req = ValidateOpenAPISchemaRequest()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.调用服务并解析对应的数据
        schema = self.api_tool_service.parse_openapi_schema(req.openapi_schema.data)
        return success_json(schema)