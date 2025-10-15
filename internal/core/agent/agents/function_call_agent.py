import json
from threading import Thread
from typing import Literal

from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage, RemoveMessage, ToolMessage
from langgraph.constants import END
from langgraph.graph.state import CompiledStateGraph, StateGraph

from internal.exception import FailedException
from .base_agent import BaseAgent
from internal.core.agent.entities.agent_entity import AgentState, AGENT_SYSTEM_PROMPT_TEMPLATE


class FunctionCallAgent(BaseAgent):
    """基于工具调用的智能体"""

    def run(self,query:str,
            history:list[AnyMessage]=None,
            long_term_memory:str="",
            ) -> str:
        if history is None:
            history = []
        agent = self._build_graph()

        thread = Thread(target=agent.invoke, args=({
            "messages": [HumanMessage(content=query)],
            "history": history,
            "long_term_memory": long_term_memory,
        }))
        thread.start()


    def _build_graph(self) -> CompiledStateGraph:
        # 创建图
        graph = StateGraph(AgentState)

        # 添加节点
        graph.add_node("long_term_memory_recall", self._long_term_memory_recall_node)
        graph.add_node("llm", self._llm_node)
        graph.add_node("tools", self._tools_node)

        # 设置边
        graph.set_entry_point("long_term_memory_recall")
        graph.add_edge("long_term_memory_recall", "llm")
        graph.add_conditional_edges("llm", self._tools_condition)
        graph.add_edge("tools", "llm")

        # 编译图
        agent = graph.compile()
        return agent


    def _long_term_memory_recall_node(self, state:AgentState) -> AgentState:
        """长期记忆召回节点"""
        # 判断是否需要召回长期记忆
        long_term_memory= ""
        if self.agent_config.enable_long_term_memory:
            long_term_memory = state["long_term_memory"]
        preset_messages = [
            SystemMessage(content=AGENT_SYSTEM_PROMPT_TEMPLATE.format(
                preset_prompt=self.agent_config.preset_prompt,
                long_term_memory=long_term_memory
            ))
        ]

        # 短期消息添加
        history = state["history"]
        if isinstance(history, list) and len(history) > 0:
            if len(history) %2 != 0:
                raise FailedException("历史消息长度必须为偶数")

            preset_messages.extend(history)

        human_message = state["messages"][-1]
        preset_messages.append(HumanMessage(human_message.content))

        # 处理预设消息
        return {
            "messages": [RemoveMessage(id=human_message.id), *preset_messages]
        }



    def _llm_node(self, state:AgentState) -> AgentState:
        """LLM节点"""
        # 从智能体配置中提取llm
        llm = self.agent_config.llm

        # 检测是否有bind_tools方法
        if (hasattr(llm, "bind_tools") and callable(getattr(llm, "bind_tools"))
                and len(self.agent_config.tools) > 0):
            llm = llm.bind_tools(self.agent_config.tools)

        # 流式调用
        gathered = None
        is_first_chunk = True
        for chunk in llm.stream(state["messages"]):
            if is_first_chunk:
                gathered = chunk
                is_first_chunk = False
            else:
                gathered += chunk

        return {"messages": gathered}




    def _tools_node(self, state:AgentState) -> AgentState:
        # 工具类别转化为字典
        tools_by_name = {tool.name: tool for tool in self.agent_config.tools}

        tool_calls = state["messages"][-1].tool_calls
        messages = []
        for tool_call in tool_calls:
            tool = tools_by_name.get(tool_call.name)
            if tool is None:
                raise FailedException(f"工具{tool_call.name}不存在")

            # 调用工具
            tool_output = tool.invoke(tool_call["args"])
            messages.append(ToolMessage(
                tool_call_id = tool_call["id"],
                content = json.dumps(tool_output),
                name = tool_call["name"]
            ))
        return {"messages": messages}



    @classmethod
    def _tools_condition(cls, state:AgentState) -> Literal["tools", "__end__"]:
        """工具条件"""
        # 提取最后一条消息
        messages = state["messages"]
        ai_message = messages[-1]

        if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
            return "tools"
        return END