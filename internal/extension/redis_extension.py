import redis
from redis.connection import Connection,SSLConnection
from flask import Flask

# redis客户端
redis_client = redis.Redis()

def init_app(app:Flask):
    """初始化redis"""
    # 检测不同的场景使用不同的连接方式
    connection_class = Connection if (app.config.get("REDIS_USE_SSL")
                                      is False) else SSLConnection

    redis_client.connection_pool = redis.ConnectionPool(
        host=app.config.get("REDIS_HOST"),
        port=app.config.get("REDIS_PORT"),
        db=app.config.get("REDIS_DB"),
        password=app.config.get("REDIS_PASSWORD"),
        username=app.config.get("REDIS_USERNAME"),
        connection_class=connection_class,
        encoding="utf-8",
        encoding_errors="strict",
        decode_responses=False,
    )

    app.extensions["redis"] = redis_client

