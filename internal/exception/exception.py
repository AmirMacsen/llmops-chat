from dataclasses import field
from typing import Any

from pkg.response import HttpCode


class CustomException(Exception):
    """自定义异常类"""

    code : HttpCode = HttpCode.FAIL
    message : str = ""
    data : Any = field(default_factory=dict)

    def __init__(self, message:str=None, data:Any=None):
        super().__init__()
        self.message = message
        self.data = data


class FailedException(CustomException):
    """通用失败异常"""


class NotFoundException(CustomException):
    """未找到异常"""
    code : HttpCode = HttpCode.NOT_FOUND


class UnauthorizedException(CustomException):
    """未授权异常"""
    code : HttpCode = HttpCode.UNAUTHORIZED

class ForbiddenException(CustomException):
    """无权限异常"""
    code : HttpCode = HttpCode.FORBIDDEN


class ValidationException(CustomException):
    """校验异常"""
    code : HttpCode = HttpCode.VALIDATE_ERROR

