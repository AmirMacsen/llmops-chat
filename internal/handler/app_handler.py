import dataclasses
import uuid
from operator import itemgetter
from typing import Any, Dict

from flask import request
from injector import inject
from langchain.memory import ConversationBufferWindowMemory
from langchain_community.chat_message_histories import FileChatMessageHistory
from langchain_core.memory import BaseMemory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda, RunnableConfig
from langchain_core.tracers import Run
from langchain_openai import ChatOpenAI

from internal.model import App
from internal.schema.app_schema import CompletionRequest
from internal.service import AppService, ApiToolService
from internal.task.demo_task import demo_task
from pkg.response import success_json, validate_error_json, success_message
from internal.core.tools.builtin_tools.providers import BuiltinProviderManager


@inject
@dataclasses.dataclass
class AppHandler(object):
    """应用处理类"""

    app_service: AppService
    provider: BuiltinProviderManager
    api_tool_service: ApiToolService

    def create_app(self):
        """
        创建应用
        ---
        tags:
          - Apps
        summary: 创建一个新的应用
        description: 创建一个新的应用实例
        responses:
          200:
            description: 成功创建应用
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    code:
                      type: integer
                      example: 200
                    message:
                      type: string
                      example: "应用已经成功创建，id为xxx"
        """
        app = self.app_service.create_app()
        return success_message(f"应用已经成功创建，id为{app.id}")

    def get_app(self, app_id:uuid.UUID):
        """
        获取应用
        ---
        tags:
          - Apps
        summary: 根据ID获取应用
        description: 根据应用ID获取特定应用的信息
        parameters:
          - name: app_id
            in: path
            description: 应用ID
            required: true
            schema:
              type: string
              format: uuid
        responses:
          200:
            description: 成功获取应用
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    code:
                      type: integer
                      example: 200
                    message:
                      type: string
                      example: "应用已经成功找到，名字为xxx"
          400:
            description: 请求参数错误
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    code:
                      type: integer
                      example: 400
                    message:
                      type: string
                      example: "应用id不能为空"
        """
        if not app_id:
            return validate_error_json(errors={'app_id': '应用id不能为空'})

        app = self.app_service.get_app(app_id)
        return success_message(f"应用已经成功找到，名字为{app.name}")


    def update_app(self, app_id:uuid.UUID) -> App:
        """
        更新应用
        ---
        tags:
          - Apps
        summary: 更新指定的应用
        description: 根据应用ID更新特定应用的信息
        parameters:
          - name: app_id
            in: path
            description: 应用ID
            required: true
            schema:
              type: string
              format: uuid
        responses:
          200:
            description: 成功更新应用
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    code:
                      type: integer
                      example: 200
                    message:
                      type: string
                      example: "应用已经成功更新，名字为xxx"
        """
        app = self.app_service.update_app(app_id)
        return success_message(f"应用已经成功更新，名字为{app.name}")


    def delete_app(self, app_id:uuid.UUID):
        """
        删除应用
        ---
        tags:
          - Apps
        summary: 删除指定的应用
        description: 根据应用ID删除特定应用
        parameters:
          - name: app_id
            in: path
            description: 应用ID
            required: true
            schema:
              type: string
              format: uuid
        responses:
          200:
            description: 成功删除应用
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    code:
                      type: integer
                      example: 200
                    message:
                      type: string
                      example: "应用已经成功删除"
        """
        self.app_service.delete_app(app_id)
        return success_message(f"应用已经成功删除")

    @classmethod
    def _load_memory_variables(cls, input: Dict[str, Any], config: RunnableConfig) -> Dict[str, Any]:
        """加载记忆变量信息"""
        configurable = config.get("configurable", {})
        configurable_memory = configurable.get("memory", None)
        if configurable_memory is not None and isinstance(configurable_memory, BaseMemory):
            return configurable_memory.load_memory_variables(input)
        return {"history": []}

    @classmethod
    def _save_context(cls, run_obj: Run, config: RunnableConfig) -> None:
        """存储对应的上下文信息到记忆实体中"""
        configurable = config.get("configurable", {})
        configurable_memory = configurable.get("memory", None)
        if configurable_memory is not None and isinstance(configurable_memory, BaseMemory):
            configurable_memory.save_context(run_obj.inputs, run_obj.outputs)

    def _get_memory(self):
        """获取对话内存实例"""
        return ConversationBufferWindowMemory(
            k=3,
            input_key="query",
            output_key="output",
            return_messages=True,
            chat_memory=FileChatMessageHistory("./storage/memory/chat_history.txt"),
        )

    def debug(self, app_id: uuid.UUID):
        """
        调试聊天接口
        ---
        tags:
          - Apps
        summary: 调试聊天功能
        description: 使用特定应用进行聊天调试
        parameters:
          - name: app_id
            in: path
            description: 应用ID
            required: true
            schema:
              type: string
              format: uuid
        requestBody:
          content:
            application/json:
              schema:
                type: object
                properties:
                  query:
                    type: string
                    example: "你好"
        responses:
          200:
            description: 成功获取响应
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
                      properties:
                        content:
                          type: string
                          example: "你好！有什么我可以帮你的吗？"
        """
        """聊天接口"""
        # 1.提取从接口中获取的输入，POST
        req = CompletionRequest()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.构建组件
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个强大的聊天机器人，能根据用户的提问回复用户的问题"),
            MessagesPlaceholder('history'),
            ("human", "{query}")
        ])
        
        # 延迟初始化 memory
        memory = self._get_memory()

        llm = ChatOpenAI(model="gpt-3.5-turbo-16k")

        chain = (RunnablePassthrough.assign(
            history=RunnableLambda(self._load_memory_variables) | itemgetter("history"),
        ) | prompt | llm | StrOutputParser()).with_listeners(on_end=self._save_context)


        # 4.调用链得到结果
        chain_input = {"query": req.query.data}
        content = chain.invoke(chain_input, config={"configurable": {"memory": memory}})

        return success_json({"content": content})

    def completion(self):
        """
        聊天接口
        ---
        tags:
          - Apps
        summary: 聊天完成接口
        description: 处理聊天请求并返回AI响应
        requestBody:
          content:
            application/json:
              schema:
                type: object
                properties:
                  query:
                    type: string
                    example: "你好"
        responses:
          200:
            description: 成功获取响应
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    code:
                      type: integer
                      example: 200
                    data:
                      type: string
                      example: "你好！有什么我可以帮你的吗？"
        """
        req = CompletionRequest()
        if not req.validate():
            return validate_error_json(errors=req.errors)
        query = request.json.get('query')
        llm = ChatOpenAI(
            model="gpt-3.5-turbo-16k",
        )
        prompt = PromptTemplate.from_template("你是一个专业的聊天助手，你的任务是回答用户的问题。问题：{query}")
        ai_message = llm.invoke(prompt.invoke({"query": query}))
        parser = StrOutputParser()
        parsed_message = parser.invoke(ai_message)
        return success_json(parsed_message)

    def ping(self):
        """
        测试接口
        ---
        tags:
          - Utils
        summary: Ping测试接口
        description: 测试接口连通性并返回提供商实体列表
        responses:
          200:
            description: 成功响应
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
        """测试方法"""
        # entities = self.provider.get_provider_entities()

        # return success_json({"ping": [p.dict() for p in entities]})

        # 调用异步任务
        demo_task.delay(uuid.uuid4())
        return self.api_tool_service.api_tool_invoke()