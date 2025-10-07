import os
from typing import List, Any

import yaml
from injector import inject,singleton
from pydantic import BaseModel, Field

from internal.core.tools.builtin_tools.entities import CategoryEntity
from internal.exception import NotFoundException


@inject
@singleton
class BuiltinCategoryManager(BaseModel):
    """内置工具的分类管理器"""
    category_map:dict[str, Any] = Field(default_factory=dict)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._init_categories()


    def get_category_map(self) -> dict[str, Any]:
        return self.category_map

    def _init_categories(self):
        """初始化内置工具分类"""
        # 检测是否已经初始化
        if self.category_map:
            return

        # 获取yml数据路径并加载
        current_path = os.path.abspath(__file__)
        category_path = os.path.dirname(current_path)
        category_yml_path = os.path.join(category_path, "categories.yml")
        with open(category_yml_path, "r", encoding="utf-8") as f:
            categories = yaml.safe_load(f)

        # 循环遍历所有分类，并将分类信息加载到实体中
        for category in categories:
            category_entity = CategoryEntity(**category)

            # 获取icon位置并检测是否存在
            icon_path = os.path.join(category_path, 'icons', category_entity.icon)
            if not os.path.exists(icon_path):
                raise NotFoundException(f"未找到图标: {icon_path}")

            # 读取图标
            with open(icon_path, "rb") as f:
                icon = f.read()

            self.category_map[category_entity.category] ={
                "entity": category_entity,
                "icon": icon
            }






