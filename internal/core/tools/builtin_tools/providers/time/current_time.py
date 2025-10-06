import datetime
from typing import Any

from langchain_core.tools import BaseTool


class CurrentTimeTool(BaseTool):
    """一个用户获取当前时间的工具"""
    name:str = 'current_time'
    description:str = '一个用于获取当前时间的工具'

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """获取当前系统的时间，并通过格式化返回"""
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')


def current_time() -> BaseTool:
    """获取当前系统时间的工具"""
    return CurrentTimeTool()
