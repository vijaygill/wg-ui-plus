"""REV-06: the MCP WireGuard configuration tool must not return the server half.

The shared generator used by the REST configuration view keeps both entries; only
the MCP tool result is trimmed so the server private key is not returned there.
"""

from unittest.mock import patch

from django.test import SimpleTestCase

from api_app import shared_functions
from api_app.mcp_tools import WireGuardMCPToolset

SERVER_CONFIGURATION = "[Interface]\nPrivateKey = SERVER-PRIVATE-KEY\n"
PEER_CONFIGURATIONS = ["[Peer]\nPrivateKey = PEER-PRIVATE-KEY\n"]


def generated_configurations(*_args, **_kwargs):
    """A fresh generator result holding both entries with sentinel values."""
    return {
        "server_configuration": SERVER_CONFIGURATION,
        "peer_configurations": list(PEER_CONFIGURATIONS),
    }


class MCPWireGuardConfigurationToolTests(SimpleTestCase):
    def setUp(self):
        self.toolset = WireGuardMCPToolset()
        self.configuration = object()

    def _call_tool(self):
        """Return the tool result together with the patched generator mock."""
        with patch.object(
            WireGuardMCPToolset, "_configuration", return_value=self.configuration
        ):
            with patch(
                "api_app.mcp_tools.get_wireguard_configuration",
                side_effect=generated_configurations,
            ) as generate:
                result = self.toolset.get_wireguard_configuration()
        return result, generate

    def test_tool_result_omits_server_configuration(self):
        result, _ = self._call_tool()
        self.assertNotIn("server_configuration", result)
        self.assertEqual(PEER_CONFIGURATIONS, result["peer_configurations"])

    def test_tool_trims_at_the_boundary_without_changing_generation(self):
        result, generate = self._call_tool()
        generate.assert_called_once_with(self.configuration)
        self.assertIn("server_configuration", generate.side_effect(self.configuration))
        self.assertEqual(PEER_CONFIGURATIONS, result["peer_configurations"])


class SharedWireGuardConfigurationUiPathTests(SimpleTestCase):
    """The REST configuration view still needs the server half."""

    def test_shared_function_still_returns_server_configuration(self):
        configuration = object()
        with patch("api_app.shared_functions.WireGuardHelper") as helper:
            helper.return_value.get_wireguard_configuration.return_value = (
                generated_configurations()
            )
            with patch("api_app.shared_functions.PeerGroup") as peer_group:
                with patch("api_app.shared_functions.Peer") as peer:
                    result = shared_functions.get_wireguard_configuration(configuration)

        self.assertIn("server_configuration", result)
        self.assertEqual(SERVER_CONFIGURATION, result["server_configuration"])
        self.assertEqual(PEER_CONFIGURATIONS, result["peer_configurations"])
        helper.return_value.get_wireguard_configuration.assert_called_once_with(
            server_configuration=configuration,
            peer_groups=peer_group.objects.all.return_value,
            peers=peer.objects.all.return_value,
        )
