from pkg.response import HttpCode
import pytest

from test.internal.conftest import client


class TestBuiltinToolHandler:
    """内部工具测试类"""

    def test_get_categories(self, client):
        """测试获取内置工具分类"""
        resp = client.get(
            "/builtin-tools/categories",
        )
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.SUCCESS
        assert resp.json.get("data")
        assert len(resp.json.get("data")) > 0


    def test_get_builtin_tools(self, client):
        """测试获取内置工具列表"""
        resp = client.get(
            "/builtin-tools",
        )
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.SUCCESS
        assert resp.json.get("data")
        assert len(resp.json.get("data")) > 0


    @pytest.mark.parametrize("provider_name, tool_name", [
        ("google", "google_serper"),
        ("openai", "text-completion"),
    ])
    def test_get_provider_tools(self, provider_name, tool_name, client):
        """测试获取服务提供商工具列表"""
        resp = client.get(
            f"/builtin-tools/{provider_name}/{tool_name}",
        )
        assert resp.status_code == 200

        if provider_name == "google":
            assert resp.json.get("code") == HttpCode.SUCCESS
            assert resp.json.get("data").get("name") == tool_name
            assert len(resp.json.get("data")) > 0
        else:
            assert resp.json.get("code") == HttpCode.NOT_FOUND

    @pytest.mark.parametrize("provider_name", [
        "google",
        "openai",
    ])
    def test_get_provider_icon(self, provider_name, client):
        """根据服务提供商的名字获取icon"""
        resp = client.get(
            f"/builtin-tools/{provider_name}/icon",
        )

        assert resp.status_code == 200

        if provider_name == "google":
            assert resp.json.get("code") == HttpCode.SUCCESS
        else:
            assert resp.json.get("code") == HttpCode.NOT_FOUND