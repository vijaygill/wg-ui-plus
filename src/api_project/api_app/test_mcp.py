import asyncio
import io
import json
import os
from datetime import datetime, timezone
from unittest.mock import PropertyMock, patch

from django.contrib.auth import get_user_model
from django.core import management
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIClient

from .mcp_authentication import MCPTokenAuthentication
from .mcp_configuration import (
    ALLOW_CHECK_UPDATES_ENV,
    MCPConfigurationService,
    MCPTokenService,
    parse_boolean_environment_value,
    parse_mcp_enabled,
)
from .mcp_tools import MCPToolError, WireGuardMCPToolset
from .models import Peer, PeerGroup, ServerConfiguration, Target
from .server_helper import get_application_details


class MCPConfigurationParsingTests(SimpleTestCase):
    def test_common_boolean_values_are_supported(self):
        for value in ("true", "1", "yes", "Y", "on"):
            self.assertTrue(parse_mcp_enabled(value))
        for value in ("false", "0", "no", "N", "off"):
            self.assertFalse(parse_mcp_enabled(value))

    def test_invalid_boolean_value_is_rejected(self):
        with self.assertRaises(ImproperlyConfigured):
            parse_mcp_enabled("maybe")

    def test_update_check_boolean_values_use_the_same_parser(self):
        self.assertTrue(parse_boolean_environment_value("YES", ALLOW_CHECK_UPDATES_ENV))
        self.assertFalse(parse_boolean_environment_value("off", ALLOW_CHECK_UPDATES_ENV))
        with self.assertRaises(ImproperlyConfigured):
            parse_boolean_environment_value("maybe", ALLOW_CHECK_UPDATES_ENV)

    @patch.dict(os.environ, {}, clear=True)
    def test_update_checks_fall_back_to_database_state(self):
        configuration = type("Configuration", (), {"allow_check_updates": True})()
        self.assertTrue(MCPConfigurationService.allow_check_updates(configuration))

    @patch.dict(os.environ, {"WG_ALLOW_CHECK_UPDATES": "false"}, clear=True)
    def test_update_check_environment_overrides_database_state(self):
        configuration = type("Configuration", (), {"allow_check_updates": True})()
        self.assertFalse(MCPConfigurationService.allow_check_updates(configuration))

    @patch.dict(os.environ, {"WG_ALLOW_CHECK_UPDATES": "invalid"}, clear=True)
    def test_invalid_update_check_environment_value_is_rejected(self):
        configuration = type("Configuration", (), {"allow_check_updates": True})()
        with self.assertRaises(ImproperlyConfigured):
            MCPConfigurationService.allow_check_updates(configuration)

    @patch.dict(os.environ, {"WG_ALLOW_CHECK_UPDATES": "invalid"}, clear=True)
    def test_application_details_rejects_invalid_update_check_environment_value(self):
        configuration = type("Configuration", (), {"allow_check_updates": True})()
        with patch("api_app.server_helper.ServerConfiguration.objects.all", return_value=[configuration]):
            with self.assertRaises(ImproperlyConfigured):
                get_application_details()

    @patch.dict(os.environ, {}, clear=True)
    def test_database_controls_state_when_environment_is_absent(self):
        with patch.object(MCPConfigurationService, "get_configuration") as get_configuration:
            get_configuration.return_value = type("Configuration", (), {"mcp_enabled": True})()
            self.assertTrue(MCPConfigurationService.is_enabled())

    @patch.dict(os.environ, {"WG_MCP_SERVER_ENABLED": "false"}, clear=True)
    def test_environment_overrides_database_state(self):
        with patch.object(MCPConfigurationService, "get_configuration") as get_configuration:
            get_configuration.return_value = type("Configuration", (), {"mcp_enabled": True})()
            self.assertFalse(MCPConfigurationService.is_enabled())


class MCPDatabaseAndStartupMixin:
    def make_configuration(self, **overrides):
        values = {
            "network_address": "192.168.2.0/24",
            "ip_address": "192.168.2.1",
            "host_name_external": "vpn.example.test",
            "port_external": 1196,
            "port_internal": 51820,
            "upstream_dns_ip_address": "192.168.0.5",
            "wireguard_config_path": "/config/wireguard/wg0.conf",
            "script_path_post_down": "/config/post-down.sh",
            "script_path_post_up": "/config/post-up.sh",
            "peer_default_port": 1196,
            "last_changed_datetime": datetime.now(timezone.utc),
        }
        values.update(overrides)
        return ServerConfiguration.objects.create(**values)

    def setUp(self):
        self.configuration = self.make_configuration()

    @patch.dict(os.environ, {}, clear=True)
    def _test_mcp_fields_have_safe_defaults(self):
        self.assertFalse(self.configuration.mcp_enabled)
        self.assertIsNone(self.configuration.mcp_token)
        self.assertFalse(MCPConfigurationService.is_enabled())

    @patch.dict(os.environ, {"WG_MCP_SERVER_ENABLED": "yes"}, clear=True)
    def _test_startup_syncs_enabled_state_generates_token_and_does_not_log_it(self):
        with self.assertLogs("api_app.mcp_configuration", level="WARNING") as logs:
            changed = MCPConfigurationService.synchronize_startup()
        self.configuration.refresh_from_db()
        self.assertTrue(changed)
        self.assertTrue(self.configuration.mcp_enabled)
        self.assertTrue(self.configuration.mcp_token)
        self.assertNotIn(self.configuration.mcp_token, "\n".join(logs.output))
        self.assertIn("new token was generated", "\n".join(logs.output))

    @patch.dict(os.environ, {"WG_MCP_SERVER_ENABLED": "not-a-boolean"}, clear=True)
    def _test_startup_rejects_invalid_environment_value(self):
        with self.assertRaises(ImproperlyConfigured):
            MCPConfigurationService.synchronize_startup()

    def _test_token_rotation_changes_only_token_and_status_masks_it(self):
        self.configuration.mcp_enabled = True
        self.configuration.save(update_fields=["mcp_enabled"])
        old_token = MCPTokenService.rotate(self.configuration)
        new_token = MCPTokenService.rotate(self.configuration)
        self.assertNotEqual(old_token, new_token)
        status = MCPConfigurationService.status(self.configuration)
        self.assertEqual("*****", status["mcp_token"])
        self.assertNotIn(new_token, json.dumps(status))


class MCPDatabaseAndStartupTests(MCPDatabaseAndStartupMixin, TestCase):
    def test_mcp_fields_have_safe_defaults(self):
        self._test_mcp_fields_have_safe_defaults()

    def test_startup_syncs_enabled_state_generates_token_and_does_not_log_it(self):
        self._test_startup_syncs_enabled_state_generates_token_and_does_not_log_it()

    def test_startup_rejects_invalid_environment_value(self):
        self._test_startup_rejects_invalid_environment_value()

    def test_token_rotation_changes_only_token_and_status_masks_it(self):
        self._test_token_rotation_changes_only_token_and_status_masks_it()


class MCPManagementCommandTests(MCPDatabaseAndStartupMixin, TestCase):
    def test_enable_generates_and_prints_only_a_missing_token(self):
        output = io.StringIO()
        management.call_command("mcp_enable", stdout=output)
        self.configuration.refresh_from_db()
        self.assertTrue(self.configuration.mcp_enabled)
        self.assertIn(self.configuration.mcp_token, output.getvalue())

        output = io.StringIO()
        management.call_command("mcp_enable", stdout=output)
        self.assertEqual("", output.getvalue())

    def test_generate_token_rotates_without_enabling_and_warns(self):
        output = io.StringIO()
        management.call_command("mcp_generate_token", stdout=output)
        self.configuration.refresh_from_db()
        self.assertFalse(self.configuration.mcp_enabled)
        self.assertIn(self.configuration.mcp_token, output.getvalue())
        self.assertIn("Previous MCP clients", output.getvalue())

    def test_disable_preserves_token(self):
        self.configuration.mcp_enabled = True
        self.configuration.mcp_token = "existing-token"
        self.configuration.save(update_fields=["mcp_enabled", "mcp_token"])
        management.call_command("mcp_disable", stdout=io.StringIO())
        self.configuration.refresh_from_db()
        self.assertFalse(self.configuration.mcp_enabled)
        self.assertEqual("existing-token", self.configuration.mcp_token)


class MCPAdministrationAndAuthenticationTests(MCPDatabaseAndStartupMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.create_user("admin", password="password")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_admin_configuration_is_authenticated_and_masks_token(self):
        self.configuration.mcp_token = "secret-token"
        self.configuration.save(update_fields=["mcp_token"])
        anonymous = APIClient().get("/api/v1/control/mcp/configuration")
        self.assertEqual(403, anonymous.status_code)
        response = self.client.get("/api/v1/control/mcp/configuration")
        self.assertEqual(200, response.status_code)
        self.assertEqual("*****", response.data["mcp_token"])
        self.assertNotIn("secret-token", response.content.decode())

    @patch.dict(os.environ, {"WG_ALLOW_CHECK_UPDATES": "false"}, clear=True)
    def test_server_configuration_metadata_reports_update_check_override(self):
        from .serializers import ServerConfigurationSerializer

        data = ServerConfigurationSerializer(self.configuration).data
        self.assertEqual("WG_ALLOW_CHECK_UPDATES", data["environment_overrides"]["allow_check_updates"])

    @patch.dict(os.environ, {"WG_ALLOW_CHECK_UPDATES": "false"}, clear=True)
    def test_server_configuration_reports_effective_update_check_value_separately(self):
        from .serializers import ServerConfigurationSerializer

        self.configuration.allow_check_updates = True
        self.configuration.save(update_fields=["allow_check_updates"])
        data = ServerConfigurationSerializer(self.configuration).data
        self.assertTrue(data["allow_check_updates"])
        self.assertFalse(data["effective_allow_check_updates"])

    def test_raw_token_copy_requires_authenticated_session(self):
        self.configuration.mcp_token = "secret-token"
        self.configuration.save(update_fields=["mcp_token"])
        self.assertEqual(403, APIClient().get("/api/v1/control/mcp/token").status_code)
        response = self.client.get("/api/v1/control/mcp/token")
        self.assertEqual(200, response.status_code)
        self.assertEqual("secret-token", response.data["mcp_token"])
        self.assertEqual("no-store, no-cache, must-revalidate", response["Cache-Control"])
        self.assertEqual("no-cache", response["Pragma"])

    def test_mcp_admin_patch_validates_boolean(self):
        response = self.client.patch(
            "/api/v1/control/mcp/configuration", {"mcp_enabled": "true"}, format="json"
        )
        self.assertEqual(400, response.status_code)
        self.assertIn("boolean", response.data["mcp_enabled"][0])


class MCPEndpointAndToolTests(MCPDatabaseAndStartupMixin, TestCase):
    MCP_PROTOCOL_VERSION = "2025-03-26"

    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.create_user("admin", password="password")
        self.configuration.mcp_enabled = True
        self.configuration.mcp_token = "mcp-secret"
        self.configuration.save(update_fields=["mcp_enabled", "mcp_token"])
        self.client = APIClient()
        self.tools = WireGuardMCPToolset()

    def mcp_request(self, payload, token=None, scheme="Token"):
        headers = {"HTTP_ACCEPT": "application/json, text/event-stream"}
        if token is not None:
            headers["HTTP_AUTHORIZATION"] = f"{scheme} {token}"
        if payload["method"] != "initialize":
            headers["HTTP_MCP_PROTOCOL_VERSION"] = self.MCP_PROTOCOL_VERSION
        return self.client.post(
            "/mcp",
            data=json.dumps(payload),
            content_type="application/json",
            **headers,
        )

    def initialize_request(self):
        return {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": self.MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "wireguard-ui-plus-tests", "version": "1.0"},
            },
        }

    def test_missing_and_invalid_mcp_tokens_are_rejected_at_http_boundary(self):
        requests = ((None, "Token"), ("wrong", "Token"), ("mcp-secret", "Basic"))
        for token, scheme in requests:
            with self.subTest(token=token, scheme=scheme):
                response = self.mcp_request(self.initialize_request(), token, scheme)
                self.assertEqual(401, response.status_code)

    def test_valid_token_and_bearer_credentials_work_at_http_boundary(self):
        for scheme in ("Token", "Bearer"):
            with self.subTest(scheme=scheme):
                response = self.mcp_request(self.initialize_request(), "mcp-secret", scheme)
                self.assertEqual(200, response.status_code)

    def test_disabled_mcp_endpoint_is_not_found(self):
        with patch.dict(os.environ, {"WG_MCP_SERVER_ENABLED": "false"}, clear=True):
            response = self.mcp_request(self.initialize_request())
        self.assertEqual(404, response.status_code)

    def test_http_initialization_returns_fixed_server_metadata(self):
        response = self.mcp_request(self.initialize_request(), "mcp-secret")
        self.assertEqual(200, response.status_code)
        self.assertEqual("application/json", response["Content-Type"])
        body = response.json()
        self.assertEqual("2.0", body["jsonrpc"])
        self.assertEqual(1, body["id"])
        self.assertEqual(self.MCP_PROTOCOL_VERSION, body["result"]["protocolVersion"])
        self.assertEqual("WireGuard UI Plus MCP Server", body["result"]["serverInfo"]["name"])

    def test_authenticated_http_tool_discovery_returns_expected_tools(self):
        initialization = self.mcp_request(self.initialize_request(), "mcp-secret")
        self.assertEqual(200, initialization.status_code)
        response = self.mcp_request(
            {"jsonrpc": "2.0", "id": 3, "method": "tools/list", "params": {}},
            "mcp-secret",
        )
        self.assertEqual(200, response.status_code)
        names = {tool["name"] for tool in response.json()["result"]["tools"]}
        self.assertIn("list_peers", names)
        self.assertIn("get_peer_configuration", names)

    def test_authenticated_http_tool_invocation_returns_tool_result(self):
        initialization = self.mcp_request(self.initialize_request(), "mcp-secret")
        self.assertEqual(200, initialization.status_code)
        response = self.mcp_request(
            {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
                "name": "list_peers", "arguments": {}
            }},
            "mcp-secret",
        )
        self.assertEqual(200, response.status_code)
        body = response.json()
        self.assertEqual(2, body["id"])
        self.assertFalse(body["result"]["isError"])
        self.assertEqual([], body["result"]["content"])

    def test_tool_not_found_and_validation_errors_are_normalized(self):
        with self.assertRaisesRegex(MCPToolError, "Peer with id 999 was not found"):
            self.tools.retrieve_peer(999)
        with self.assertRaisesRegex(MCPToolError, "Invalid target"):
            self.tools.create_target({"name": "bad", "ip_address": "not-an-ip"})

    def test_safe_peer_outputs_omit_private_material_and_sensitive_tools_are_separate(self):
        peer = Peer.objects.create(
            name="Laptop",
            description="test",
            private_key="private-key",
            public_key="public-key",
            ip_address="192.168.2.2",
            port=1196,
        )
        ordinary = self.tools.retrieve_peer(peer.id)
        self.assertNotIn("private_key", ordinary)
        self.assertNotIn("configuration", ordinary)
        self.assertNotIn("qr", ordinary)
        with patch("api_app.mcp_tools.PeerWithQrSerializer.data", new_callable=PropertyMock) as data:
            data.return_value = {"configuration": "[Interface]", "qr": b"cX"}
            self.assertEqual("[Interface]", self.tools.get_peer_configuration(peer.id)["configuration"])
            self.assertEqual("cX", self.tools.get_peer_qr(peer.id)["qr"])

    def test_relationships_and_crud_return_safe_records(self):
        group = self.tools.create_peer_group({"name": "Operators", "peer_ids": [], "target_ids": []})
        target = self.tools.create_target({"name": "Router", "ip_address": "192.168.0.1:22", "peer_group_ids": []})
        updated = self.tools.update_peer_group(group["id"], {"target_ids": [target["id"]]})
        self.assertEqual([target["id"]], updated["target_ids"])
        self.assertEqual(target["id"], self.tools.delete_target(target["id"])["id"])

    def test_toolset_is_discoverable_by_django_mcp_server(self):
        from mcp_server.djangomcp import global_mcp_server

        names = {tool.name for tool in asyncio.run(global_mcp_server.list_tools())}
        self.assertIn("list_peers", names)
        self.assertIn("get_peer_configuration", names)
