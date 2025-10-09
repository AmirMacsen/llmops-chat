from dotenv import load_dotenv
from flask_migrate import Migrate
from injector import Injector, Module, Binder

from .module import ExtensionModule
from internal.router import Router
from internal.server import Http
from config import Config
from pkg.sqlalchemy import SQLAlchemy



load_dotenv(dotenv_path='.env')

config = Config()



injector = Injector([ExtensionModule])

app = Http(
    __name__,
    config=config,
    db=injector.get(SQLAlchemy),
    migrate=injector.get(Migrate),
    router=injector.get(Router))


celery = app.extensions["celery"]

if __name__ == '__main__':
    app.run(debug=True)
