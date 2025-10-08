import pytest

from internal.model import ApiToolProvider
from pkg.response import HttpCode
from test.internal.conftest import client

openapi_schema_right = """
{"server":"http://baidu.com","description":"baidu","paths":{"/location":{"get":{"description":"获取位置信息","operationId":"xxxx","parameters":[{"name":"location","description":"位置信息","in":"query","required":true,"type":"str"}]}}}}
"""

openapi_schema_wrong = """
{"server":"http://baidu.com","description":"baidu","paths":{"/location":{"get":{"description":"获取位置信息","operationId":"xxxx","parameters":[{"name111":"location","description":"位置信息","in":"query","required":true,"type":"str"}]}}}}
"""

class TestApiToolHandler:
    """测试API工具处理器"""

    @pytest.mark.parametrize("openapi_schema", [openapi_schema_right, openapi_schema_wrong])
    def test_parse_openapi_schema(self, openapi_schema, client):
        """测试解析OpenAPI规范"""
        resp = client.post(
            "/api-tools/validate-openapi-schema",
            json={
                "openapi_schema": openapi_schema
            },
        )
        assert resp.status_code == 200

        resp_json = resp.get_json()
        if openapi_schema == openapi_schema_right:
            assert resp_json.get("code") == HttpCode.SUCCESS.value
            assert resp_json.get("data")
        else:
            assert resp_json.get("code") == HttpCode.VALIDATE_ERROR.value

    @pytest.mark.parametrize("provider_id", [
        "b03d55b5-895e-47c8-b767-6d0015ae60a1",
        "3944eee4-9d5a-4ca5-91c1-e56654cbc1e5"
    ])
    def test_get_api_tool_provider(self, provider_id, client):
        resp = client.get(f"/api-tools/{provider_id}")
        assert resp.status_code == 200
        if provider_id.endswith("4"):
            assert resp.json.get("code") == HttpCode.SUCCESS
        elif provider_id.endswith("5"):
            assert resp.json.get("code") == HttpCode.NOT_FOUND

    @pytest.mark.parametrize("provider_id, tool_name", [
        ("b03d55b5-895e-47c8-b767-6d0015ae60a1", "GetLocationForIp"),
        ("3944eee4-9d5a-4ca5-91c1-e56654cbc1e4", "google")
    ])
    def test_get_api_tool(self, provider_id, tool_name, client):
        resp = client.get(f"/api-tools/{provider_id}/tools/{tool_name}")
        assert resp.status_code == 200
        if tool_name == "GetLocationForIp":
            assert resp.json.get("code") == HttpCode.SUCCESS
        elif tool_name == "google":
            assert resp.json.get("code") == HttpCode.NOT_FOUND

    def test_create_api_tool_provider(self, client, db):
        data = {
            "name": "Google工具包",
            "icon": "https://cdn.google.com/icon.png",
            "openapi_schema": "{\"description\":\"查询ip所在地、天气预报、路线规划等高德工具包\",\"server\":\"https://gaode.example.com\",\"paths\":{\"/weather\":{\"get\":{\"description\":\"根据传递的城市名获取指定城市的天气预报，例如：广州\",\"operationId\":\"GetCurrentWeather\",\"parameters\":[{\"name\":\"location\",\"in\":\"query\",\"description\":\"需要查询天气预报的城市名\",\"required\":true,\"type\":\"str\"}]}},\"/ip\":{\"post\":{\"description\":\"根据传递的ip查询ip归属地\",\"operationId\":\"GetCurrentIp\",\"parameters\":[{\"name\":\"ip\",\"in\":\"request_body\",\"description\":\"需要查询所在地的标准ip地址，例如:201.52.14.23\",\"required\":true,\"type\":\"str\"}]}}}}",
            "headers": [{"key": "Authorization", "value": "Bearer access_token"}]
        }
        resp = client.post("/api-tools", json=data)
        assert resp.status_code == 200

        from internal.model import ApiToolProvider
        api_tool_provider = db.session.query(ApiToolProvider).filter_by(name="Google工具包").one_or_none()
        assert api_tool_provider is not None

    def test_update_api_tool_provider(self, client, db):
        provider_id = "b03d55b5-895e-47c8-b767-6d0015ae60a1"
        data = {
            "name": "test_update_api_tool_provider",
            "icon": "https://cdn.google.com/icon.png",
            "openapi_schema": "{\"description\":\"查询ip所在地、天气预报、路线规划等高德工具包\",\"server\":\"https://gaode.example.com\",\"paths\":{\"/weather\":{\"get\":{\"description\":\"根据传递的城市名获取指定城市的天气预报，例如：广州\",\"operationId\":\"GetCurrentWeather\",\"parameters\":[{\"name\":\"location\",\"in\":\"query\",\"description\":\"需要查询天气预报的城市名\",\"required\":true,\"type\":\"str\"}]}},\"/ip\":{\"post\":{\"description\":\"根据传递的ip查询ip归属地\",\"operationId\":\"GetLocationForIp\",\"parameters\":[{\"name\":\"ip\",\"in\":\"request_body\",\"description\":\"需要查询所在地的标准ip地址，例如:201.52.14.23\",\"required\":true,\"type\":\"str\"}]}}}}",
            "headers": [{"key": "Authorization", "value": "Bearer access_token"}]
        }
        resp = client.post(f"/api-tools/{provider_id}", json=data)
        assert resp.status_code == 200

        from internal.model import ApiToolProvider
        api_tool_provider = db.session.query(ApiToolProvider).get(provider_id)
        assert api_tool_provider.name == data.get("name")

    def test_delete_api_tool_provider(self, client, db):
        provider_id = "b03d55b5-895e-47c8-b767-6d0015ae60a1"
        resp = client.post(f"/api-tools/{provider_id}/delete")
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.SUCCESS

        from internal.model import ApiToolProvider
        api_tool_provider = db.session.query(ApiToolProvider).get(provider_id)
        assert api_tool_provider is None
