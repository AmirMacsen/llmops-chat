import pytest
from sqlalchemy.orm import sessionmaker, scoped_session

from internal.extension.database_extension import db as _db

@pytest.fixture
def app():
    """获取flask的测试应用"""
    from app.http.app import app as _app
    _app.config['TESTING'] = True
    return _app

@pytest.fixture
def client(app):
    """获取flask的测试应用"""
    from app.http.app import app
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def db(app):
    """创建临时的数据库会话，操作结束回滚"""

    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()

        session_factory = sessionmaker(bind=connection)
        session = scoped_session(session_factory)
        _db.session = session
        yield _db
        transaction.rollback()
        connection.close()
        session.remove()
