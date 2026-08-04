import os

from django.core.management.base import BaseCommand, CommandError

from api_app.mcp_configuration import MCPConfigurationService, MCPTokenService, MCP_SERVER_ENABLED_ENV


class Command(BaseCommand):
    help = "Rotate the MCP client token without changing the enabled state."

    def handle(self, *args, **options):
        configuration = MCPConfigurationService.get_configuration()
        if configuration is None:
            raise CommandError("ServerConfiguration is not initialized; no token was generated.")
        token = MCPTokenService.rotate(configuration)
        self.stdout.write(token)
        self.stdout.write(self.style.WARNING("Previous MCP clients must be updated."))
        if MCP_SERVER_ENABLED_ENV in os.environ:
            self.stdout.write(self.style.WARNING(f"{MCP_SERVER_ENABLED_ENV} may override database enabled state on startup."))
