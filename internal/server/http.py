import os

from flask import Flask
from flask_migrate import Migrate
from flask_cors import CORS
from flasgger import Swagger

from config import Config
from internal.exception import CustomException
from internal.router import Router
from pkg.response import Response, json, HttpCode
from pkg.sqlalchemy import SQLAlchemy


class Http(Flask):
    """http服务器"""
    def __init__(
            self,
            *args,
            config: Config,
            db:SQLAlchemy,
            migrate:Migrate,
            router:Router,
            **kwargs):
        super(Http, self).__init__(*args, **kwargs)

        # 加载配置
        self.config.from_object(config)

        # 初始化Swagger
        self.config['SWAGGER'] = {
            'title': 'LlmOps API',
            'uiversion': 3,
            'openapi': '3.0.2',
            'version': '1.0.0',
            'description': 'LlmOps API Documentation',
            'termsOfService': ''
        }
        self.swagger = Swagger(self)

        # 异常处理
        self.register_error_handler(Exception, self._register_error_handler)

        # 初始化数据库
        db.init_app(self)
        migrate.init_app(self, db, directory='internal/migrations')

        # 解决前后端跨域问题
        CORS(self, resources={r"/*": {
            "origins": "*",
            "supports_credentials": True,
            # "methods": ["GET", "POST", "PUT", "DELETE"],
            # "allowed_headers": ["Content-Type"]
            }
        })

        # 注册路由
        router.register_router(self)


    def _register_error_handler(self, error:Exception):
        """注册异常处理函数"""
        # 判断异常信息是否是自定义异常
        if isinstance(error, CustomException):
            return json(Response(
                code=error.code,
                message=error.message,
                data=error.data if hasattr(error, 'data') else None,
            ))
        # 如果不是自定义，比如数据库异常等，提取信息，返回FAIL状态
        if self.debug or os.environ.get('DEBUG'):
            raise error
        return json(Response(
            code=HttpCode.FAIL,
            message=str(error),
            data={}
        ))