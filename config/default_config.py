## 应用默认配置

DEFAULT_CONFIG = {
    # CSRF 配置
    'WTF_CSRF_ENABLED': "False",

    # SQLALCHEMY 数据库配置信息
    'SQLALCHEMY_DATABASE_URI': "postgresql://root:root@localhost:5432/llmops?client_encoding=utf8",
    'SQLALCHEMY_ECHO': "True",
    'SQLALCHEMY_POOL_RECYCLE': 3600,
    'SQLALCHEMY_POOL_SIZE': 10,

    # REDIS 数据库配置信息
    'REDIS_HOST': "localhost",
    'REDIS_PORT': 6379,
    'REDIS_DB': 0,
    'REDIS_PASSWORD': "",
    'REDIS_USERNAME': "",
    'REDIS_USE_SSL': "False",

    # celery 默认配置
    "CELERY_BROKER_DB": 1,
    "CELERY_RESULT_DB": 1,
    "CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP": "True",
    "CELERY_TASK_IGNORE_RESULT": "False",
    "CELERY_RESULT_EXPIRES": 60 * 60 * 1,
}
