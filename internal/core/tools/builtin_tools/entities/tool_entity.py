from enum import Enum
from typing import Optional, Any, List

from pydantic import BaseModel, Field


class ToolParamType(Enum):
    """工具参数类型枚举"""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    SELECT = "select"


class ToolParam(BaseModel):
    """工具参数"""
    name:str # 参数的实际名字
    label:str # 参数的展示标签
    type:ToolParamType # 参数的类型
    required:bool = False # 是否必填
    default:Optional[Any]= None # 默认值
    min: Optional[float] = None
    max: Optional[float] = None
    options: list[dict[str,Any]] = Field(default_factory=list)

class ToolEntity(BaseModel):
    """工具实体类，映射的是工具名.yaml中的数据"""
    name:str
    label:str
    description:str
    params: list[ToolParam]=Field(default_factory=list)# 工具参数
