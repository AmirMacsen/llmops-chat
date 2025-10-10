from flask_migrate import Migrate
from redis import Redis

from internal.extension.migrate_extension import migrate
from pkg.sqlalchemy import SQLAlchemy
from injector import Module, Binder, Injector

from internal.extension.database_extension import db
from internal.extension.redis_extension import redis_client


class ExtensionModule(Module):
    """扩展模块的依赖注入"""
    def configure(self, binder: Binder):
        binder.bind(SQLAlchemy, to=db)
        binder.bind(Migrate, to=migrate)
        binder.bind(Redis, to=redis_client)



injector = Injector([ExtensionModule])