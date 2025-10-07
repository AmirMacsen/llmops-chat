import pytest

from pkg.response import HttpCode


class TestAppHandler:

    @pytest.mark.parametrize(
        "app_id, query",
        [
            ("a23241c4-b3c1-4f09-8759-e9afbd9f10e4", None),
            ("a23241c4-b3c1-4f09-8759-e9afbd9f10e4", "你好,你是谁？"),
        ]
    )
    def test_debug(self,app_id, query, client):
        """测试completion接口"""
        resp = client.post(
            f"/apps/{app_id}/debug",
            json={"query": query}
        )
        assert resp.status_code == 200
        if query is None:
            assert resp.json.get("code") == HttpCode.VALIDATE_ERROR
        else:
            assert resp.json.get("code") == HttpCode.SUCCESS
