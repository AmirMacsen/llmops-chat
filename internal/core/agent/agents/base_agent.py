import uuid
from abc import abstractmethod
from threading import Thread
from typing import Optional, Any, Iterator

from langchain_core.language_models import BaseLanguageModel
from langchain_core.load import Serializable
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.runnables.utils import Input
from langgraph.graph.state import CompiledStateGraph
from pydantic import PrivateAttr

from internal.core.agent.entities.agent_entity import AgentConfig
from internal.exception import FailedException
from .agent_queue_manager import AgentQueueManager
from ..entities.queue_entity import AgentResult, AgentThought, QueueEvent


class BaseAgent(Serializable, Runnable):
    """
    Abstract base class for all agents.
    """
    llm: BaseLanguageModel
    agent_config: AgentConfig
    _agent: CompiledStateGraph = PrivateAttr(None)
    _agent_queue_manager: AgentQueueManager = PrivateAttr(None)

    class Config:
        """Config for BaseAgent"""
        arbitrary_types_allowed = True

    def __init__(
            self,
            llm: BaseLanguageModel,
            agent_config: AgentConfig,
            *args,
            **kwargs
    ):
        """构造函数，初始化智能体图结构程序"""
        super().__init__(*args, llm=llm, agent_config=agent_config, **kwargs)
        self._agent = self._build_agent()
        self._agent_queue_manager = AgentQueueManager(
            user_id=agent_config.user_id,
            invoke_from=agent_config.invoke_from,
        )

    @abstractmethod
    def _build_agent(self) -> CompiledStateGraph:
        """
        Build the agent graph structure.
        """
        raise NotImplementedError("Agent的构建函数未实现")


    def invoke(
        self,
        input: Input,
        config: Optional[RunnableConfig] = None,
        **kwargs: Any,
    ) -> AgentResult:
        """块内容响应"""
        # 调用stream方法获取流式数据输出
        agent_result = AgentResult(query=input["messages"][0].content)
        agent_thoughts = {}

        for agent_thought in self.stream(input, config):
            # 提取事件id
            event_id = str(agent_thought.id)
            # 除了ping事件其他事件全部记录
            if agent_thought.event != QueueEvent.PING:
                # 单独处理agent message事件，因为需要叠加返回数据
                if agent_thought.event == QueueEvent.AGENT_MESSAGE:
                    if event_id not in agent_thoughts:
                        agent_thoughts[event_id] = agent_thought
                    else:
                        agent_thoughts[event_id] = agent_thoughts[event_id].model_copy(update={
                            "thought": agent_thoughts[event_id].thought + agent_thought.thought,
                            "answer": agent_thoughts[event_id].answer + agent_thought.answer,
                            "latency": agent_thought.latency
                        })
                    # 更新智能体消息答案
                    agent_result.answer += agent_thought.answer
                else:
                    # 其他类型的事件直接覆盖
                    agent_thoughts[event_id] = agent_thought

                    # 处理特殊事件
                    if agent_thought.event in [QueueEvent.STOP, QueueEvent.ERROR, QueueEvent.TIMEOUT]:
                        agent_result.status = agent_thought.event
                        agent_result.error = agent_thought.observation if agent_thought.event == QueueEvent.ERROR else ""

        agent_result.agent_thoughts = [agent_thought for agent_thought in agent_thoughts.values()]

        agent_result.message = next(
            (agent_thought.message for agent_thought in agent_thoughts.values()
             if agent_thought.event == QueueEvent.AGENT_MESSAGE),
            []
        )

        agent_result.latency = sum([agent_thought.latency for agent_thought in agent_thoughts.values()])

        return agent_result


    def stream(
        self,
        input: Input,
        config: Optional[RunnableConfig] = None,
        **kwargs: Optional[Any],
    ) -> Iterator[AgentThought]:
        """流式输出"""
        # 检测子类是否已经构建agent
        if not self._agent:
            raise FailedException("智能体未构建")

        # 构建对应的任务id并初始化
        input["task_id"] = input.get("task_id", str(uuid.uuid4()))
        input["history"] = input.get("history", [])
        input["iteration_count"] = input.get("iteration_count", 0)

        # 创建子线程并执行
        thread = Thread(
            target=self._agent.invoke,
            args=(input,),
            kwargs=kwargs,
        )
        thread.start()

        # 监听队列
        yield from self._agent_queue_manager.listen(input["task_id"])

    @property
    def agent_queue_manager(self) -> AgentQueueManager:
        """获取队列管理器"""
        return self._agent_queue_manager