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

        # redis配置
        self.REDIS_HOST = _get_env('REDIS_HOST')
        self.REDIS_PORT = _get_env('REDIS_PORT')
        self.REDIS_PASSWORD = _get_env('REDIS_PASSWORD')
        self.REDIS_DB = _get_env('REDIS_DB')
        self.REDIS_USERNAME = _get_env('REDIS_USERNAME')
        self.REDIS_USE_SSL = _get_bool_env('REDIS_USE_SSL')

        # celery配置
        self.CELERY = {
            "broker_url": f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{int(_get_env('CELERY_BROKER_DB'))}",
            "result_backend": f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{int(_get_env('CELERY_RESULT_DB'))}",
            "task_ignore_result": _get_bool_env("CELERY_TASK_IGNORE_RESULT"),
            "result_expires": int(_get_env("CELERY_RESULT_EXPIRES")),
            "broker_connection_retry_on_startup": _get_bool_env("CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP"),
        }
