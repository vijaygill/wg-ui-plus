import secrets

from django.contrib.auth import get_user_model
from rest_framework.authentication import get_authorization_header, TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .mcp_configuration import MCPConfigurationService


class MCPTokenAuthentication(TokenAuthentication):
    """Validate the MCP token stored by the application configuration.

    The application-managed credential is not a DRF authtoken row. Both the
    traditional DRF ``Token`` scheme and the ``Bearer`` scheme used by Open
    WebUI are accepted for the MCP endpoint.
    """

    accepted_schemes = frozenset((b"token", b"bearer"))

    def authenticate(self, request):
        """Authenticate an MCP request using either supported auth scheme."""
        auth = get_authorization_header(request).split()
        if not auth:
            return None
        if auth[0].lower() not in self.accepted_schemes:
            raise AuthenticationFailed("Invalid token header. Unsupported authentication scheme.")
        if len(auth) == 1:
            raise AuthenticationFailed("Invalid token header. No credentials provided.")
        if len(auth) > 2:
            raise AuthenticationFailed("Invalid token header. Token string should not contain spaces.")
        try:
            key = auth[1].decode()
        except UnicodeError:
            raise AuthenticationFailed("Invalid token header. Token string should not contain invalid characters.")
        return self.authenticate_credentials(key)

    def authenticate_credentials(self, key):
        configuration = MCPConfigurationService.get_configuration()
        if configuration is None or not configuration.mcp_token or not secrets.compare_digest(key, configuration.mcp_token):
            raise AuthenticationFailed("Invalid MCP token.")
        user = get_user_model().objects.filter(is_active=True).order_by("id").first()
        if user is None:
            raise AuthenticationFailed("No active user is available for MCP access.")
        return (user, key)
