import uuid
from dataclasses import dataclass

from injector import inject
from pkg.sqlalchemy import SQLAlchemy

from internal.model import App


@inject
@dataclass
class AppService:
    db: SQLAlchemy

    def create_app(self)->App:
        with self.db.auto_commit():
            app = App(name="测试机器人",account_id=uuid.uuid4(), icon="icon.png", description="这是一个测试机器人")
            self.db.session.add(app)
        return app

    def get_app(self, app_id: uuid.UUID)->App:
        return self.db.session.query(App).get(app_id)


    def update_app(self, app_id:uuid.UUID)-> App:
        with self.db.auto_commit():
            app = self.get_app(app_id)
            app.name = "测试机器人2"
        return app

    def delete_app(self, app_id:uuid.UUID)->None:
        with self.db.auto_commit():
            app = self.get_app(app_id)
            self.db.session.delete(app)
