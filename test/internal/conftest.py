import pytest


@pytest.fixture
def client():
    """获取flask的测试应用"""
    from app.http.app import app
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
