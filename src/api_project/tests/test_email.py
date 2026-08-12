import base64
from datetime import datetime, timezone
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIClient

from api_app.email_service import (
    EmailRecipientError,
    email_peer_configuration,
    get_email_status,
    parse_smtp_configuration,
    send_configuration_email,
    validate_recipient,
)
from api_app.mcp_tools import WireGuardMCPToolset
from api_app.models import Peer, ServerConfiguration


class SMTPConfigurationTests(SimpleTestCase):
    def valid_environment(self):
        return {
            "EMAIL_HOST": "smtp.gmail.com",
            "EMAIL_HOST_USER": "sender@gmail.com",
            "EMAIL_HOST_PASSWORD": "secret",
            "EMAIL_PORT": "587",
            "EMAIL_USE_TLS": "True",
            "EMAIL_USE_SSL": "False",
        }

    def test_configuration_is_typed_and_sender_falls_back_to_user(self):
        configuration = parse_smtp_configuration(self.valid_environment())
        self.assertEqual(587, configuration.port)
        self.assertTrue(configuration.use_tls)
        self.assertFalse(configuration.use_ssl)
        self.assertEqual("sender@gmail.com", configuration.from_email)

    def test_invalid_boolean_and_conflicting_transport_are_rejected(self):
        values = self.valid_environment()
        values["EMAIL_USE_TLS"] = "maybe"
        with self.assertRaises(ImproperlyConfigured):
            parse_smtp_configuration(values)
        values.update(EMAIL_USE_TLS="true", EMAIL_USE_SSL="true")
        with self.assertRaises(ImproperlyConfigured):
            parse_smtp_configuration(values)

    def test_non_strict_parsing_keeps_startup_safe_for_partial_configuration(self):
        values = self.valid_environment()
        values.pop("EMAIL_HOST_PASSWORD")
        self.assertIsNone(parse_smtp_configuration(values, require_complete=False))
        with patch.dict("os.environ", values, clear=True):
            self.assertEqual("invalid", get_email_status()["status"])

    def test_disabled_security_modes_are_rejected(self):
        values = self.valid_environment()
        values.update(EMAIL_USE_TLS="false", EMAIL_USE_SSL="false")
        with self.assertRaises(ImproperlyConfigured):
            parse_smtp_configuration(values)

    def test_invalid_sender_and_default_sender_are_rejected(self):
        values = self.valid_environment()
        values["EMAIL_HOST_USER"] = "not-an-email"
        with self.assertRaises(ImproperlyConfigured):
            parse_smtp_configuration(values)

        values = self.valid_environment()
        values["EMAIL_DEFAULT_FROM_EMAIL"] = "also-not-an-email"
        with patch.dict("os.environ", values, clear=True):
            self.assertEqual("invalid", get_email_status()["status"])
        with self.assertRaises(ImproperlyConfigured):
            parse_smtp_configuration(values)

    def test_capability_status_distinguishes_unavailable_and_invalid(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual("unavailable", get_email_status()["status"])
        values = self.valid_environment()
        values["EMAIL_PORT"] = "not-a-port"
        with patch.dict("os.environ", values, clear=True):
            self.assertEqual("invalid", get_email_status()["status"])

    def test_recipient_is_required_and_validated(self):
        with self.assertRaises(EmailRecipientError):
            validate_recipient("")
        with self.assertRaises(EmailRecipientError):
            validate_recipient("not-an-email")


class EmailDeliveryTests(SimpleTestCase):
    @patch.dict("os.environ", {
        "EMAIL_HOST": "smtp.gmail.com", "EMAIL_HOST_USER": "sender@gmail.com",
        "EMAIL_HOST_PASSWORD": "secret", "EMAIL_PORT": "587",
        "EMAIL_USE_TLS": "true", "EMAIL_USE_SSL": "false",
    }, clear=True)
    @patch("api_app.email_service.EmailMessage")
    def test_sender_attaches_configuration_and_qr(self, email_class):
        message = email_class.return_value
        qr = base64.b64encode(b"exact-png-content")
        send_configuration_email("subject", "body", "peer@gmail.com", qr, "exact-conf-content")
        email_class.assert_called_once()
        self.assertEqual("peer@gmail.com", email_class.call_args.kwargs["to"][0])
        self.assertEqual([
            ("tunnel.conf", "exact-conf-content", "text/plain"),
            ("tunnel.png", b"exact-png-content", "image/png"),
        ], [call.args for call in message.attach.call_args_list])
        message.send.assert_called_once_with(fail_silently=False)


class PeerEmailEndpointTests(TestCase):
    def setUp(self):
        self.configuration = ServerConfiguration.objects.create(
            network_address="192.168.2.0/24", ip_address="192.168.2.1",
            host_name_external="vpn.example.test", port_external=1196,
            port_internal=51820, upstream_dns_ip_address="192.168.0.5",
            wireguard_config_path="/config/wg0.conf",
            script_path_post_down="/config/post-down.sh",
            script_path_post_up="/config/post-up.sh", peer_default_port=1196,
            last_changed_datetime=datetime.now(timezone.utc),
        )
        self.peer = Peer.objects.create(name="Laptop", email_address="saved@example.com")
        user = get_user_model().objects.create_user("admin", password="password")
        self.client = APIClient()
        self.client.force_authenticate(user=user)

    @patch("api_app.email_service.send_configuration_email")
    @patch("api_app.serializers.PeerWithQrSerializer")
    @patch.dict("os.environ", {
        "EMAIL_HOST": "smtp.gmail.com", "EMAIL_HOST_USER": "sender@gmail.com",
        "EMAIL_HOST_PASSWORD": "secret", "EMAIL_PORT": "587",
        "EMAIL_USE_TLS": "true", "EMAIL_USE_SSL": "false",
    }, clear=True)
    def test_endpoint_rejects_payload_overrides_and_delivers_stored_peer_data(
        self, serializer_class, send
    ):
        serializer_class.return_value.data = {
            "configuration": "server-generated-config",
            "qr": base64.b64encode(b"server-generated-qr"),
        }
        response = self.client.post("/api/v1/data/peer/send_peer_email", {
            "peer_id": self.peer.id, "email_address": "attacker@example.com",
            "qr": "attacker", "configuration": "attacker",
        }, format="json")
        self.assertEqual(400, response.status_code)
        send.assert_not_called()

        response = self.client.post("/api/v1/data/peer/send_peer_email",
                                    {"peer_id": self.peer.id}, format="json")
        self.assertEqual(200, response.status_code)
        send.assert_called_once_with(
            "Tunnel configuration sent from wg-ui-plus for Laptop",
            "The WireGuard configuration for Laptop is attached. Keep it safe.",
            "saved@example.com",
            base64.b64encode(b"server-generated-qr"),
            "server-generated-config",
        )

    def test_endpoint_requires_authentication(self):
        response = APIClient().post("/api/v1/data/peer/send_peer_email",
                                    {"peer_id": self.peer.id}, format="json")
        self.assertEqual(403, response.status_code)

    @patch("api_app.email_service.send_configuration_email")
    @patch("api_app.serializers.PeerWithQrSerializer")
    @patch.dict("os.environ", {
        "EMAIL_HOST": "smtp.gmail.com", "EMAIL_HOST_USER": "sender@gmail.com",
        "EMAIL_HOST_PASSWORD": "secret", "EMAIL_PORT": "587",
        "EMAIL_USE_TLS": "true", "EMAIL_USE_SSL": "false",
    }, clear=True)
    def test_peer_delivery_uses_saved_recipient_and_server_generated_payload(
        self, serializer_class, send
    ):
        serializer_class.return_value.data = {
            "configuration": "server-generated-config",
            "qr": base64.b64encode(b"server-generated-qr"),
        }
        email_peer_configuration(self.peer)
        send.assert_called_once_with(
            "Tunnel configuration sent from wg-ui-plus for Laptop",
            "The WireGuard configuration for Laptop is attached. Keep it safe.",
            "saved@example.com",
            base64.b64encode(b"server-generated-qr"),
            "server-generated-config",
        )


class MCPEmailTests(PeerEmailEndpointTests):
    @patch("api_app.mcp_tools.email_peer_configuration")
    def test_mcp_uses_saved_peer_and_rejects_override_argument(self, send):
        result = WireGuardMCPToolset().send_peer_configuration_email(self.peer.id)
        self.assertEqual("Email sent successfully!", result["message"])
        send.assert_called_once_with(self.peer)
        with self.assertRaises(TypeError):
            WireGuardMCPToolset().send_peer_configuration_email(
                self.peer.id, "attacker@example.com"
            )
