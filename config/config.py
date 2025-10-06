import os
from typing import Any

from config.default_config import DEFAULT_CONFIG


def _get_env(key:str) ->Any:
    """获取环境变量"""
    return os.getenv(key, DEFAULT_CONFIG.get(key))


def _get_bool_env(key:str) ->Any:
    """获取布尔类型环境变量"""
    return _get_env(key).lower() == 'true'


class Config:
    def __init__(self):
        # 关闭wtf的csrf校验
        self.WTF_CSRF_ENABLED = _get_bool_env("WTF_CSRF_ENABLED")

        # 数据库配置
        self.SQLALCHEMY_DATABASE_URI = _get_env('SQLALCHEMY_DATABASE_URI')
        self.SQLALCHEMY_ECHO = _get_bool_env('SQLALCHEMY_ECHO')
        self.SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': int(_get_env('SQLALCHEMY_POOL_SIZE')),
            'pool_recycle': int(_get_env('SQLALCHEMY_POOL_RECYCLE')),
        }
