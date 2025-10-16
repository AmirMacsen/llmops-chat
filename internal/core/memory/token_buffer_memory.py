from dataclasses import dataclass

from langchain_core.messages import (
    AnyMessage,AIMessage,HumanMessage,
    trim_messages, get_buffer_string
)
from sqlalchemy import desc

from internal.entity.conversation_entity import MessageStatus
from internal.model import Conversation, Message
from pkg.sqlalchemy import SQLAlchemy
from langchain_core.language_models import BaseLanguageModel


@dataclass
class TokenBufferMemory:
    """基于token计数的缓存记忆组件"""
    db: SQLAlchemy
    conversation:Conversation
    model_instance: BaseLanguageModel


    def get_history_prompt_messages(
            self, max_token_count: int = 2000,
            message_limit: int = 10
    ) -> list[AnyMessage]:
        """根据传递的token限制和条数限制，获取指定会话的消息列表"""
        if self.conversation is None:
            return []

        # 查询会话消息列表，倒叙，而且答案不为空+未删除+状态正常
        messages = self.db.session.query(Message).filter(
            Message.conversation_id == self.conversation.id,
            Message.answer != "",
            Message.is_deleted == False,
            Message.status.in_([MessageStatus.NORMAL, MessageStatus.STOP, MessageStatus.TIMEOUT])
        ).order_by(desc("created_at")).limit(message_limit).all()

        messages = list(reversed(messages))

        # 转化成lcdocument列表
        prompt_messages = []
        for message in messages:
            prompt_messages.extend([
                HumanMessage(content=message.query),
                AIMessage(content=message.answer),
            ])

        # 调用langchain的工具剪切消息
        return trim_messages(
            prompt_messages,
            max_tokens=max_token_count,
            token_counter=self.model_instance,
            strategy="last"
        )


    def get_history_prompt_text(
            self, human_prefix:str = "Human",
            ai_prefix:str = "AI",
            max_token_count: int = 2000,
            message_limit: int = 10
    ):
        """根据传递的token限制和条数限制，获取指定会话的消息列表"""
        message = self.get_history_prompt_messages(max_token_count, message_limit)

        return get_buffer_string(message, human_prefix, ai_prefix)
