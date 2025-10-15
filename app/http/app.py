from dotenv import load_dotenv
from flask_login import LoginManager
from flask_migrate import Migrate

from config import Config
from internal.middleware import Middleware
from internal.router import Router
from internal.server import Http
from pkg.sqlalchemy import SQLAlchemy
from .module import injector

load_dotenv(dotenv_path='.env')

config = Config()


app = Http(
    __name__,
    config=config,
    db=injector.get(SQLAlchemy),
    migrate=injector.get(Migrate),
    login_manager=injector.get(LoginManager),
    middleware=injector.get(Middleware),
    router=injector.get(Router))


celery = app.extensions["celery"]

if __name__ == '__main__':
    app.run(debug=True)
