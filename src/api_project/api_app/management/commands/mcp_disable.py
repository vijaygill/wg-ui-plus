import os

from django.core.management.base import BaseCommand, CommandError

from api_app.mcp_configuration import MCPConfigurationService, MCP_SERVER_ENABLED_ENV


class Command(BaseCommand):
    help = "Disable MCP while preserving its token."

    def handle(self, *args, **options):
        configuration = MCPConfigurationService.get_configuration()
        if configuration is None:
            raise CommandError("ServerConfiguration is not initialized; MCP was not disabled.")
        configuration.mcp_enabled = False
        configuration.save(update_fields=["mcp_enabled"])
        if MCP_SERVER_ENABLED_ENV in os.environ:
            self.stdout.write(self.style.WARNING(f"{MCP_SERVER_ENABLED_ENV} may override database enabled state on startup."))
