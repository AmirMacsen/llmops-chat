from langchain_community.tools.openai_dalle_image_generation import OpenAIDALLEImageGenerationTool
from langchain_core.tools import BaseTool
from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper
from pydantic import BaseModel, Field


class DALLE3ArgsSchema(BaseModel):
    query:str = Field(description="用于图文生成描述信息")

def dalle3(**kwargs)->BaseTool:
    """返回dalle3绘图的工具"""
    return OpenAIDALLEImageGenerationTool(
        api_wrapper=DallEAPIWrapper(
            model="dall-e-3",
            **kwargs,
        ),
        args_schema=DALLE3ArgsSchema,
    )