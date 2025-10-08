import pytest
from unittest.mock import patch, MagicMock
from uuid import UUID

from test.internal.conftest import client
from pkg.response import HttpCode

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

    def test_create_open_ai_tool_success(self, client):
        """测试成功创建OpenAI工具"""
        # 准备测试数据
        test_data = {
            "name": "Test API Tool",
            "icon": "https://example.com/icon.png",
            "openapi_schema": openapi_schema_right
        }
        
        # 发送POST请求
        resp = client.post(
            "/api-tools",
            json=test_data,
        )
        
        # 验证响应状态码
        assert resp.status_code == 200
        resp_json = resp.get_json()
        assert resp_json.get("code") == HttpCode.SUCCESS.value
        assert resp_json.get("data") == "创建自定义插件成功"

    def test_create_open_ai_tool_validation_error(self, client):
        """测试创建OpenAI工具时的验证错误"""
        # 准备无效的测试数据（缺少必需字段）
        test_data = {
            "name": "",  # 无效：空名称
            "icon": "invalid-url",  # 无效：不是有效的URL
            "openapi_schema": ""  # 无效：空schema
        }
        
        # 发送POST请求
        resp = client.post(
            "/api-tools",
            json=test_data,
        )
        
        # 验证响应状态码和错误码
        assert resp.status_code == 200
        resp_json = resp.get_json()
        assert resp_json.get("code") == HttpCode.VALIDATE_ERROR.value

    @patch('internal.handler.api_tool_handler.ApiToolService')
    def test_get_api_tool_provider_success(self, mock_service, client):
        """测试成功获取API工具提供商"""
        # 准备测试数据
        provider_id = "123e4567-e89b-12d3-a456-426614174000"
        
        # 创建模拟的provider对象
        mock_provider = MagicMock()
        mock_provider.id = UUID(provider_id)
        mock_provider.name = "Test Provider"
        mock_provider.icon = "https://example.com/icon.png"
        mock_provider.openapi_schema = openapi_schema_right
        mock_provider.headers = []
        
        # 设置服务层返回值
        mock_service_instance = mock_service.return_value
        mock_service_instance.get_api_tool_provider.return_value = mock_provider
        
        # 发送GET请求
        resp = client.get(f"/api-tools/{provider_id}")
        
        # 验证响应
        assert resp.status_code == 200
        resp_json = resp.get_json()
        assert resp_json.get("code") == HttpCode.SUCCESS.value
        assert "data" in resp_json
        data = resp_json.get("data")
        assert str(data.get("id")) == provider_id
        assert data.get("name") == "Test Provider"
        assert data.get("icon") == "https://example.com/icon.png"

    @patch('internal.handler.api_tool_handler.ApiToolService')
    def test_get_api_tool_provider_not_found(self, mock_service, client):
        """测试获取不存在的API工具提供商"""
        # 准备测试数据
        provider_id = "123e4567-e89b-12d3-a456-426614174000"
        
        # 设置服务层抛出异常
        mock_service_instance = mock_service.return_value
        mock_service_instance.get_api_tool_provider.side_effect = Exception("provider未找到")
        
        # 发送GET请求
        resp = client.get(f"/api-tools/{provider_id}")
        
        # 验证响应（这里根据实际异常处理逻辑可能需要调整）
        assert resp.status_code == 200