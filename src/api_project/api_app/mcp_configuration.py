import logging
import os
import secrets

from django.core.exceptions import ImproperlyConfigured

from .models import ServerConfiguration

logger = logging.getLogger(__name__)
MCP_SERVER_ENABLED_ENV = "WG_MCP_SERVER_ENABLED"
ALLOW_CHECK_UPDATES_ENV = "WG_ALLOW_CHECK_UPDATES"
TRUE_VALUES = {"true", "1", "yes", "y", "on"}
FALSE_VALUES = {"false", "0", "no", "n", "off"}
MCP_SERVER_NAME = "WireGuard UI Plus MCP Server"


def parse_mcp_enabled(value):
    normalized = str(value).strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    raise ImproperlyConfigured(
        f"{MCP_SERVER_ENABLED_ENV} must be a boolean (true/false, 1/0, yes/no)."
    )


def parse_boolean_environment_value(value, environment_name):
    normalized = str(value).strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    raise ImproperlyConfigured(
        f"{environment_name} must be a boolean (true/false, 1/0, yes/no)."
    )


class MCPTokenService:
    @staticmethod
    def generate_token():
        return secrets.token_urlsafe(48)

    @classmethod
    def rotate(cls, configuration):
        configuration.mcp_token = cls.generate_token()
        configuration.save(update_fields=["mcp_token"])
        return configuration.mcp_token


class MCPConfigurationService:
    @staticmethod
    def get_configuration():
        return ServerConfiguration.objects.first()

    @classmethod
    def environment_value(cls):
        if MCP_SERVER_ENABLED_ENV not in os.environ:
            return None
        return parse_mcp_enabled(os.environ[MCP_SERVER_ENABLED_ENV])

    @classmethod
    def allow_check_updates_environment_value(cls):
        if ALLOW_CHECK_UPDATES_ENV not in os.environ:
            return None
        return parse_boolean_environment_value(
            os.environ[ALLOW_CHECK_UPDATES_ENV], ALLOW_CHECK_UPDATES_ENV
        )

    @classmethod
    def allow_check_updates(cls, configuration):
        environment_value = cls.allow_check_updates_environment_value()
        return configuration.allow_check_updates if environment_value is None else environment_value

    @classmethod
    def is_enabled(cls):
        configuration = cls.get_configuration()
        if configuration is None:
            return False
        environment_value = cls.environment_value()
        return configuration.mcp_enabled if environment_value is None else environment_value

    @classmethod
    def synchronize_startup(cls):
        configuration = cls.get_configuration()
        if configuration is None:
            raise ImproperlyConfigured("MCP startup requires a ServerConfiguration row.")
        environment_value = cls.environment_value()
        changed = False
        if environment_value is not None and configuration.mcp_enabled != environment_value:
            configuration.mcp_enabled = environment_value
            configuration.save(update_fields=["mcp_enabled"])
            changed = True
        if cls.is_enabled() and not configuration.mcp_token:
            MCPTokenService.rotate(configuration)
            logger.warning(
                "MCP is enabled but had no token. A new token was generated; copy it from the MCP Server page."
            )
            changed = True
        return changed

    @classmethod
    def status(cls, configuration):
        environment_value = cls.environment_value()
        return {
            "mcp_enabled": configuration.mcp_enabled,
            "effective_enabled": cls.is_enabled(),
            "environment_override": environment_value is not None,
            "environment_enabled": environment_value,
            "mcp_token": "*****" if configuration.mcp_token else None,
        }
