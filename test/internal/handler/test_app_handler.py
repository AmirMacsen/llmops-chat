import pytest

from pkg.response import HttpCode


class TestAppHandler:

    @pytest.mark.parametrize("query", [None, "你好，你是谁"])
    def test_completion(self,query, client):
        """测试completion接口"""
        resp = client.post(
            "/completion",
            json={
                "query": query
            }
        )
        print("11111", resp.json)
        assert resp.status_code == 200
        if query is None:
            assert resp.json.get("code") == HttpCode.VALIDATE_ERROR
        else:
            assert resp.json.get("code") == HttpCode.SUCCESS
