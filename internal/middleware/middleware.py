from typing import Optional

from flask import Request
from injector import inject
from dataclasses import dataclass

from internal.exception import UnauthorizedException
from internal.model import Account
from internal.service import JwtService, AccountService


@inject
@dataclass
class Middleware:
    """中间件"""
    jwt_service: JwtService
    account_service: AccountService

    def request_loader(self, request:Request)->Optional[Account]:
        """登录处理"""
        if request.blueprint == "llmops":
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                raise UnauthorizedException("未找到认证信息")

            # 请求信息中没有空格分隔符，则验证失败
            if " " not in auth_header:
                raise UnauthorizedException("认证信息格式错误")

            # 分割授权信息符合格式
            auth_schema, access_token = auth_header.split(" ")
            if auth_schema != "Bearer":
                raise UnauthorizedException("认证信息格式错误")

            # 解析token
            payload = self.jwt_service.parse_token(access_token)
            account_id = payload.get("sub")
            return self.account_service.get_account(account_id)
        else:
            return None
