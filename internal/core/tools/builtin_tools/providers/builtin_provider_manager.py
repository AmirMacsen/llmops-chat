import os.path
from typing import Any, List

import yaml
from injector import singleton, inject
from pydantic import Field

from internal.core.tools.builtin_tools.entities import ProviderEntity, Provider, ToolEntity


@inject
@singleton
class BuiltinProviderManager(object):
    """服务提供商工厂类"""

    def __init__(self, **kwargs):
        """实例化服务提供商工厂类"""
        super().__init__(**kwargs)
        self.provider_map: dict[str, Provider] = {}
        self._get_provider_tool_map()

    def get_provider(self, provider_name:str) -> Provider:
        return self.provider_map.get(provider_name)


    def get_providers(self) -> list[Provider]:
        print(self.provider_map)
        return list(self.provider_map.values())

    def get_provider_entities(self) -> List[ProviderEntity]:
        return [provider.provider_entity for provider in self.provider_map.values()]

    def get_tool(self, provider_name:str, tool_name:str) -> Any:
        provider = self.get_provider(provider_name)
        if not provider:
            return None
        return provider.get_tool(tool_name)

    def _get_provider_tool_map(self):
        """项目初始化时获取服务提供商、工具的映射关系并填充provider"""
        if self.provider_map:
            return self

        current_path = os.path.abspath(__file__)
        providers_path = os.path.dirname(current_path)
        providers_yml_path = os.path.join(providers_path, "providers.yml")

        with open(providers_yml_path, "r", encoding="utf-8") as f:
            provider_yml_data = yaml.safe_load(f)

        for idx, provider_data in enumerate(provider_yml_data):
            provider_entity = ProviderEntity(**provider_data)
            self.provider_map[provider_entity.name] = Provider(
                name=provider_entity.name,
                position=idx+1,
                provider_entity=provider_entity
            )