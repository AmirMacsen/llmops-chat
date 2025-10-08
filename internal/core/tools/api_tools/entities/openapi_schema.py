from enum import Enum

from pydantic import BaseModel, Field, field_validator
from internal.exception import ValidationException



class ParameterIn(str,Enum):
    """参数位置枚举"""
    QUERY = "query"
    PATH = "path"
    HEADER = "header"
    COOKIE = "cookie"
    REQUEST_BODY = "body"


class ParameterType(str,Enum):
    """参数类型枚举"""
    STRING = "str"
    Float = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    INT = "int"


ParameterTypeMap = {
    ParameterType.STRING: str,
    ParameterType.Float: float,
    ParameterType.BOOLEAN: bool,
    ParameterType.ARRAY: list,
    ParameterType.OBJECT: dict,
    ParameterType.INT: int
}


class OpenAPISchema(BaseModel):
    """OpenAPI接口协议规范的输入"""
    description:str = Field(default="", description="工具提供者的描述信息", validate_default=True)
    server:str = Field(default="", description="工具提供者的服务地址", validate_default=True)
    paths: dict[str, dict] = Field(default_factory=dict, description="工具提供者提供的接口", validate_default=True)

    @field_validator("server", mode="before")
    def validate_server(cls, server: str) -> str:
        """校验服务地址"""
        if server is None or server == "":
            raise ValidationException("server不能为空")

        return server

    @field_validator("description", mode="before")
    def validate_description(cls, description: str) -> str:
        """校验描述信息"""
        if description is None or description == "":
            raise ValidationException("description不能为空")

        return description

    @field_validator("paths", mode="before")
    def validate_paths(cls, paths: dict) -> dict:
        """校验路径信息"""
        if paths is None or not isinstance(paths, dict):
            raise ValidationException("path不能为空且为字典")

        # 提取paths中的元素，并获取元素下的get/post元素的值
        interfaces = []
        extra_paths = {}
        for path, path_item in paths.items():
            for method in ["get", "post"]:
                if method in path_item:
                   interfaces.append({
                       "path": path,
                       "method": method,
                       "operation": path_item[method]
                   })

        # 遍历提取到的所有接口，并进行数据格式检测
        operation_ids = []
        for interface in interfaces:
            if not isinstance(interface["operation"].get("description"), str):
                raise ValidationException(f"{interface['path']}的{interface['method']}接口的description字段必须为字符串")
            if not isinstance(interface["operation"].get("operationId"), str):
                raise ValidationException(f"{interface['path']}的{interface['method']}接口的operationId字段必须为字符串")
            if not isinstance(interface["operation"].get("parameters",[]), list):
                raise ValidationException(f"{interface['path']}的{interface['method']}接口的parameters字段必须为列表")

            # 检测operationId
            if interface["operation"]["operationId"] in operation_ids:
                raise ValidationException(f"{interface['path']}的{interface['method']}接口的operationId字段不能重复")
            operation_ids.append(interface["operation"]["operationId"])

            # 校验参数格式是否正确
            for parameter in interface["operation"].get("parameters", []):
                # 校验 name/in/description/required/type参数是否存在，且类型正确
                if not isinstance(parameter.get("name"), str):
                    raise ValidationException(f"{interface['path']}的{interface['method']}接口的parameters字段的name字段必须为字符串")
                if not isinstance(parameter.get("description"), str):
                    raise ValidationException(f"{interface['path']}的{interface['method']}接口的parameters字段的description字段必须为字符串")
                if not isinstance(parameter.get("required"), bool):
                    raise ValidationException(f"{interface['path']}的{interface['method']}接口的parameters字段的required字段必须为布尔值")
                if not isinstance(parameter.get("in"), str) or parameter["in"] not in ParameterIn.__members__.values():
                    raise ValidationException(f"{interface['path']}的{interface['method']}接口的parameters字段的in字段必须为字符串，且只能为{ParameterIn}")

                if not isinstance(parameter.get("type"), str) or parameter["type"] not in ParameterType.__members__.values():
                    raise ValidationException(f"{interface['path']}的{interface['method']}接口的parameters字段的type字段必须为字符串，且只能为{ParameterType}")

             # 组装数据并更新
            extra_paths[interface["path"]] = {
                interface["method"]: {
                    "description": interface["operation"]["description"],
                    "operationId": interface["operation"]["operationId"],
                    "parameters": [{
                        "name": parameter["name"],
                        "description": parameter["description"],
                        "required": parameter["required"],
                        "in": parameter["in"],
                        "type": parameter["type"]
                    } for parameter in interface["operation"].get("parameters", [])]
                }
            }
        return extra_paths