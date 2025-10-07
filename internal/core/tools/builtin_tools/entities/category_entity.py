from pydantic import BaseModel, field_validator

from internal.exception import FailedException


class CategoryEntity(BaseModel):
    """内置工具分类实体"""
    category:str # 分类
    name:str # 分类名称
    icon:str # 分类图标名称

    @field_validator("icon")
    def validate_icon(cls, v):
        """验证图标名称"""
        if not v.endswith(".svg"):
            raise FailedException("必须是svg图片")
        return v