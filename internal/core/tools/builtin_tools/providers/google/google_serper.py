from langchain_community.tools import GoogleSerperRun
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class GoogleSerperArgsSchema(BaseModel):
    """google serper 搜索参数描述"""
    query: str = Field(description="需要检索的查询语句")


def google_serper(**kwargs) -> BaseTool:
    """google serper 搜索"""
    return GoogleSerperRun(
        name="google_serper",
        description="这是一个低成本的google搜索API。当你需要搜索时事的时候就可以使用，输出信息是一个查询语句。",
        args_schema=GoogleSerperArgsSchema,
        api_wrapper=GoogleSerperAPIWrapper()
    )