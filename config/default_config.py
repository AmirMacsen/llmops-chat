## 应用默认配置

DEFAULT_CONFIG = {
    # CSRF 配置
    'WTF_CSRF_ENABLED': "False",
    # SQLALCHEMY 数据库配置信息
    'SQLALCHEMY_DATABASE_URI': "postgresql://root:root@localhost:5432/llmops?client_encoding=utf8",
    'SQLALCHEMY_ECHO': "True",
    'SQLALCHEMY_POOL_RECYCLE': 3600,
    'SQLALCHEMY_POOL_SIZE': 10,
}
