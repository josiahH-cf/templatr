"""Tests for Protocol interfaces.

Verifies that Protocol classes exist, are runtime_checkable, and that
concrete classes satisfy isinstance() checks.
"""

from templatr.core.interfaces import (
    ConfigManagerProtocol,
    LLMClientProtocol,
    LLMServerProtocol,
    TemplateManagerProtocol,
)


class TestProtocolsExist:
    """Verify Protocol classes exist and are runtime_checkable."""

    def test_config_manager_protocol_exists(self):
        assert hasattr(ConfigManagerProtocol, "__protocol_attrs__") or hasattr(
            ConfigManagerProtocol, "__abstractmethods__"
        ) or isinstance(ConfigManagerProtocol, type)

    def test_template_manager_protocol_exists(self):
        assert isinstance(TemplateManagerProtocol, type)

    def test_llm_client_protocol_exists(self):
        assert isinstance(LLMClientProtocol, type)

    def test_llm_server_protocol_exists(self):
        assert isinstance(LLMServerProtocol, type)


class TestConcreteClassesSatisfyProtocols:
    """Verify concrete classes satisfy their Protocol via isinstance()."""

    def test_config_manager_satisfies_protocol(self, tmp_config_dir):
        from templatr.core.config import ConfigManager

        manager = ConfigManager(config_path=tmp_config_dir / "config.json")
        assert isinstance(manager, ConfigManagerProtocol)

    def test_template_manager_satisfies_protocol(self, tmp_templates_dir):
        from templatr.core.templates import TemplateManager

        manager = TemplateManager(templates_dir=tmp_templates_dir)
        assert isinstance(manager, TemplateManagerProtocol)

    def test_llm_client_satisfies_protocol(self):
        from templatr.integrations.llm import LLMClient

        client = LLMClient("http://localhost:9999")
        assert isinstance(client, LLMClientProtocol)

    def test_llm_server_satisfies_protocol(self):
        from templatr.integrations.llm import LLMServerManager

        server = LLMServerManager()
        assert isinstance(server, LLMServerProtocol)
