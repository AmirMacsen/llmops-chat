from pydantic import BaseModel, Field


class ToolEntity(BaseModel):
    """API工具实体信息，记录了创建langchain工具所需的字段"""
    id: str = Field(default="", description="API工具提供者对应的ID")
    name: str = Field(default="", description="API工具名称")
    url: str = Field(default="", description="API工具对应的URL")
    method: str = Field(default="get", description="API工具对应的请求方法")
    description: str = Field(default="", description="API工具描述")
    headers: list[dict] = Field(default_factory=list, description="API工具对应的请求头")
    parameters: list[dict] = Field(default_factory=list, description="API工具对应的请求参数")

