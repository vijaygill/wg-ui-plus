from django.core.management.base import BaseCommand, CommandError

from api_app.mcp_configuration import MCPConfigurationService


class Command(BaseCommand):
    help = "Synchronize MCP startup configuration and create a missing token when enabled."

    def handle(self, *args, **options):
        try:
            MCPConfigurationService.synchronize_startup()
        except Exception as exc:
            raise CommandError(str(exc)) from exc
