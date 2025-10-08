from typing import Type, Optional, Callable

import requests
from injector import inject
from dataclasses import dataclass

from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel, create_model, Field

from internal.core.tools.api_tools.entities import ToolEntity, ParameterTypeMap, ParameterIn


@inject
@dataclass
class ApiProviderManager(BaseModel):
    """
    API工具提供者管理器, 可以根据传递工具配置信息生成自定义的langchain工具
    """

    @classmethod
    def _create_model_from_parameters(cls, parameters: list[dict]) -> Type[BaseModel]:
        """根据参数列表生成pydantic模型"""
        fields = {}
        for parameter in parameters:
            field_name = parameter.get("name")
            field_type = ParameterTypeMap.get(parameter.get("type"), str)
            field_required = parameter.get("required", True)
            field_description = parameter.get("description", "")
            fields[field_name] = (
                field_type if field_required else Optional[field_type],
                Field(description=field_description)
            )

        return create_model(
            "DynamicModel", **fields
        )

    @classmethod
    def _create_tool_func_from_tool_entity(cls, tool_entity: ToolEntity)->Callable:
        """根据函数传递的信息创建发起API请求的函数"""
        def _tool_func(**kwargs)->str:
            """API请求工具的函数"""
            parameters = {
                ParameterIn.PATH: {},
                ParameterIn.HEADER: {},
                ParameterIn.QUERY: {},
                ParameterIn.REQUEST_BODY: {},
                ParameterIn.COOKIE: {}
            }

            parameter_map= {parameter.get("name"):parameter for parameter in tool_entity.parameters}
            header_map = {header.get("key"):header.get("value") for header in tool_entity.headers}

            for key, value in kwargs.items():
                parameter = parameter_map.get(key)
                if parameter is None:
                    continue
                parameters[parameter.get("in", ParameterIn.QUERY)][key] = value
            return requests.request(
                method=tool_entity.method,
                url=tool_entity.url.format(**parameters[ParameterIn.PATH]),
                params=parameters[ParameterIn.QUERY],
                headers={**header_map, **parameters[ParameterIn.HEADER]},
                json=parameters[ParameterIn.REQUEST_BODY],
                cookies=parameters[ParameterIn.COOKIE]
            ).text


        return _tool_func

    def get_tool(self, tool_entity: ToolEntity)->BaseTool:
        """根据工具实体获取工具"""
        return StructuredTool.from_function(
            func=self._create_tool_func_from_tool_entity(tool_entity),
            name=f"{tool_entity.id}_{tool_entity.name}",
            description=tool_entity.description,
            args_schema=self._create_model_from_parameters(tool_entity.parameters)
        )
