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
from internal.service import AppService
from pkg.response import success_json, validate_error_json, success_message
from internal.core.tools.builtin_tools.providers import BuiltinProviderManager


@inject
@dataclasses.dataclass
class AppHandler(object):
    """应用处理类"""

    app_service: AppService
    provider: BuiltinProviderManager

    def create_app(self):
        """
        创建应用
        :return:
        """
        app = self.app_service.create_app()
        return success_message(f"应用已经成功创建，id为{app.id}")

    def get_app(self, app_id:uuid.UUID):
        """
        获取应用
        :param app_id: 应用id
        :return:
        """
        if not app_id:
            return validate_error_json(errors={'app_id': '应用id不能为空'})

        app = self.app_service.get_app(app_id)
        return success_message(f"应用已经成功找到，名字为{app.name}")


    def update_app(self, app_id:uuid.UUID) -> App:
        """
        更新应用
        :param app_id: 应用id
        :return:
        """
        app = self.app_service.update_app(app_id)
        return success_message(f"应用已经成功更新，名字为{app.name}")


    def delete_app(self, app_id:uuid.UUID):
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

    def debug(self, app_id: uuid.UUID):
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
        memory = ConversationBufferWindowMemory(
            k=3,
            input_key="query",
            output_key="output",
            return_messages=True,
            chat_memory=FileChatMessageHistory("./storage/memory/chat_history.txt"),
        )

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
        :return:
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
        """测试方法"""
        entities = self.provider.get_provider_entities()
        return success_json({"ping": [p.dict() for p in entities]})
