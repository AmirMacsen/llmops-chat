import os.path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from .tool_entity import ToolEntity
from internal.lib.helper import dynamic_import


class ProviderEntity(BaseModel):
    """服务提供商实体"""
    name:str # 名字
    label:str  # 标签
    description:str # 描述
    icon:str # 图标
    background:str # 图标的颜色
    category:str # 分类信息
    created_at: int = 0 # 提供商/工具的创建时间戳



class Provider(BaseModel):
    """服务提供商，可以在该类下获取到所有该服务提供商的工具、描述、图标等信息"""
    name:str
    position: int # 服务提供商的顺序
    provider_entity:ProviderEntity  # 服务提供商实体
    tool_entity_map: dict[str, ToolEntity] = Field(default_factory=dict)  # 工具实体映射表
    tool_func_map: dict[str, Any]= Field(default_factory=dict)# 工具函数映射表


    def __init__(self, **kwargs: Any):
        """构造函数，完成服务提供商的初始化"""
        super().__init__(**kwargs)
        self._provider_init()

    class Config:
        protected_namespace=("name",)


    def get_tool(self, tool_name:str) ->Any:
        """根据工具的名字获取对应的工具"""
        return self.tool_func_map[tool_name]

    def get_tool_entity(self, tool_name:str) -> ToolEntity:
        """根据工具的名字获取工具的实体"""
        return self.tool_entity_map[tool_name]

    def get_tool_entities(self)->list[ToolEntity]:
        return list(self.tool_entity_map.values())

    def _provider_init(self):
        """服务提供商初始化"""
        current_path = os.path.abspath(__file__)
        entities_path = os.path.dirname(current_path)
        provider_path = os.path.join(os.path.dirname(entities_path), "providers", self.name)

        # 组装获取position.yml数据
        position_yml_path = os.path.join(provider_path, "positions.yml")

        with open(position_yml_path, "r", encoding="utf-8") as f:
            positions_yml_data = yaml.safe_load(f)


        # 循环读取位置信息，获取服务提供商的名字
        for tool_name in positions_yml_data:
            # 获取工具的yml路径
            tool_yml_path = os.path.join(provider_path, f"{tool_name}.yml")
            with open(tool_yml_path, "r", encoding="utf-8") as f:
                tool_yml_data = yaml.safe_load(f)
            self.tool_entity_map[tool_name] = ToolEntity(**tool_yml_data)

            # 动态导入工具，并填充到tool_func_map中
            self.tool_func_map[tool_name] = dynamic_import(
                f"internal.core.tools.builtin_tools.providers.{self.name}",
                tool_name)




