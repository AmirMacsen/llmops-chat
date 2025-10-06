from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class DuckDuckGoSearchInput(BaseModel):
    query: str = Field(description="搜索查询语句")

def duckduckgo_search(**kwargs)->BaseTool:
    """duckduckgo search 工具"""
    return DuckDuckGoSearchRun(
        description="一个注重隐私的搜索工具，当你需要进行网路搜索时，可以使用这个工具，工具的输入是一个查询语句。",
        args_schema=DuckDuckGoSearchInput,
    )