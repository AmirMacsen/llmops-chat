from datetime import datetime
import hashlib
import importlib
from typing import Any

from langchain_core.documents import Document


def dynamic_import(module_name:str, symbol_name:str) -> Any:
    """动态导入特定模块下的特定功能"""
    module = importlib.import_module(module_name)
    return getattr(module, symbol_name)


def add_attribute(attr_name:str, attr_value:Any):
    def decorator(func):
        setattr(func, attr_name, attr_value)
        return func
    return decorator


def generate_text_hash(text:str):
    """根据传递的文本计算hash"""
    # 将需要计算hash值的内容+none，避免空字符串
    text = text + "None"
    # 使用sha3_256算法计算hash值
    return hashlib.sha3_256(text.encode("utf-8")).hexdigest()


def datetime_to_timestamp(dt:datetime) -> int:
    """将datetime转换为时间戳, 如果数据不存在，返回0"""
    if dt is None:
        return 0
    return int(dt.timestamp())


def combine_documents(documents: list[Document]) -> str:
    """将对应的文档列表使用换行符进行合并"""
    return "\n\n".join([document.page_content for document in documents])

def remove_fields(data_dict: dict, fields: list[str]) -> None:
    """根据传递的字段名移除字典中指定的字段"""
    for field in fields:
        data_dict.pop(field, None)


