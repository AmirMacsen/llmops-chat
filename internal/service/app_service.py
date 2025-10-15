import uuid
from dataclasses import dataclass
from uuid import UUID

from injector import inject
from pkg.sqlalchemy import SQLAlchemy

from internal.model import App, Account
from internal.exception import NotFoundException


@inject
@dataclass
class AppService:
    db: SQLAlchemy

    def create_app(self, account: Account = None)->App:
        account_id = str(account.id) if account else str(uuid.uuid4())
            
        with self.db.auto_commit():
            app = App(name="测试机器人",account_id=account_id, icon="icon.png", description="这是一个测试机器人")
            self.db.session.add(app)
        return app

    def get_app(self, app_id: UUID, account: Account = None)->App:
        account_id = str(account.id) if account else "b03d55b5-895e-47c8-b767-6d0015ae60a1"
        
        app = self.db.session.query(App).get(app_id)
        if app is None or str(app.account_id) != account_id:
            raise NotFoundException("应用不存在")
        return app


    def update_app(self, app_id:UUID, account: Account = None)-> App:
        account_id = str(account.id) if account else "b03d55b5-895e-47c8-b767-6d0015ae60a1"
        
        app = self.get_app(app_id, account)
        if str(app.account_id) != account_id:
            raise NotFoundException("应用不存在")
            
        with self.db.auto_commit():
            app.name = "测试机器人2"
        return app

    def delete_app(self, app_id:UUID, account: Account = None)->None:
        account_id = str(account.id) if account else "b03d55b5-895e-47c8-b767-6d0015ae60a1"
        
        app = self.get_app(app_id, account)
        if str(app.account_id) != account_id:
            raise NotFoundException("应用不存在")
            
        with self.db.auto_commit():
            self.db.session.delete(app)