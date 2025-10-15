from abc import ABC, abstractmethod

from langchain_core.messages import AnyMessage

from internal.core.agent.entities.agent_entity import AgentConfig


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    """
    agent_config: AgentConfig

    def __init__(self, agent_config: AgentConfig):
        self.agent_config = agent_config

    @abstractmethod
    def run(self,query:str,
            history:list[AnyMessage]=None,
            long_term_memory:str="",
            ) -> str:
        """
        Run the agent with the given input.
        """
        raise NotImplementedError("Agent的运行函数未实现")
