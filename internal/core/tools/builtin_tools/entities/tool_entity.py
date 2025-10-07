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
    
    def model_dump(self, *args, **kwargs):
        """重写model_dump方法，确保type字段能正确序列化"""
        dump = super().model_dump(*args, **kwargs)
        dump['type'] = self.type.value
        return dump

class ToolEntity(BaseModel):
    """工具实体类，映射的是工具名.yaml中的数据"""
    name:str
    label:str
    description:str
    params: list[ToolParam]=Field(default_factory=list)# 工具参数
    
    def model_dump(self, *args, **kwargs):
        """重写model_dump方法，确保嵌套的ToolParam能正确序列化"""
        dump = super().model_dump(*args, **kwargs)
        dump['params'] = [param.model_dump() for param in self.params]
        return dump