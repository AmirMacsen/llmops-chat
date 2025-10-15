import dataclasses
import json
import uuid
from queue import Queue
from threading import Thread
from typing import Any, Dict, Generator

from flask import request
from flask_login import login_required, current_user
from injector import inject
from langchain.memory import ConversationBufferWindowMemory
from langchain_community.chat_message_histories import FileChatMessageHistory
from langchain_core.memory import BaseMemory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_core.tracers import Run
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState

from internal.core.tools.builtin_tools.providers import BuiltinProviderManager
from internal.model import App
from internal.schema.app_schema import CompletionRequest
from internal.service import AppService, ApiToolService, ConversationService
from pkg.response import success_json, validate_error_json, success_message


@inject
@dataclasses.dataclass
class AppHandler(object):
    """应用处理类"""

    app_service: AppService
    builtin_provider_manager: BuiltinProviderManager
    api_tool_service: ApiToolService
    conversation_service: ConversationService

    @login_required
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
        app = self.app_service.create_app(account=current_user)
        return success_message(f"应用已经成功创建，id为{app.id}")

    @login_required
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

        app = self.app_service.get_app(app_id, account=current_user)
        return success_message(f"应用已经成功找到，名字为{app.name}")


    @login_required
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
        app = self.app_service.update_app(app_id, account=current_user)
        return success_message(f"应用已经成功更新，名字为{app.name}")


    @login_required
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

    @classmethod
    def _get_memory(cls):
        """获取对话内存实例"""
        return ConversationBufferWindowMemory(
            k=3,
            input_key="query",
            output_key="output",
            return_messages=True,
            chat_memory=FileChatMessageHistory("./storage/memory/chat_history.txt"),
        )

    def debug(self, app_id: uuid.UUID):
        """流式输出接口"""
        req = CompletionRequest()
        if not req.validate():
            return validate_error_json(req.errors)
        # 创建队列，并提取query
        q = Queue()
        query = req.query.data

        # 创建graph
        def graph_app() -> None:
            # 创建tools工具列表
            tools = [
                self.builtin_provider_manager.get_tool("google", "google_serper")(),
                self.builtin_provider_manager.get_tool("google", "google_weather")(),
                self.builtin_provider_manager.get_tool("dalle", "dalle3")(),
            ]

            # 定义llm
            def  chatbot(state:MessagesState) -> MessagesState:
                llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7).bind_tools(tools)

                # 调用stream
                is_first_chunk=True
                is_tool_call=False
                gathered = None
                id = str(uuid.uuid4())
                for chunk in llm.stream(state["messages"]):
                    # 检测是否是第一个块
                    if is_first_chunk and chunk.content == "" and not chunk.tool_calls:
                        continue
                    # 叠加块内容
                    if is_first_chunk:
                        gathered = chunk
                        is_first_chunk = False
                    else:
                        gathered +=  chunk

                    # # 判断是工具调用还是文本生成
                    # if tool_call or is_tool_call:
                    #     is_tool_call = True
                    #     id = str(uuid.uuid4())
                    #     tool = tools_by_name[tool_call["name"]]
                    #     q.put({
                    #         "id": id,
                    #         "event": "agent_thought",
                    #         "data": json.dumps(chunk.tool_call_chunk)
                    #     })


        def stream_event_response() -> Generator:
            """流式事件输出响应"""
            while True:
                item = q.get()
                if item is None:
                    break
                yield f"evnet: {item.get('event')}\ndata: {json.dumps(item)}\n\n"
                q.task_done()

        t = Thread(target=graph_app)
        t.start()

    @login_required
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
        from internal.core.agent.agents import FunctionCallAgent
        from internal.core.agent.entities.agent_entity import AgentConfig
        from langchain_openai import ChatOpenAI
        agent = FunctionCallAgent(AgentConfig(
            llm = ChatOpenAI(model="gpt-4o-mini"),
        ))
        state = agent.run("你好", [], "")
        content = state["messages"][-1].content

        return success_json({"content": content})