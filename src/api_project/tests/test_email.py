import base64
import smtplib
import socket
import ssl
from datetime import datetime, timezone
from unittest.mock import call, patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, TestCase, override_settings
from rest_framework.test import APIClient

from api_app.email_service import (
    EMAIL_DELIVERY_AUTHENTICATION_MESSAGE,
    EMAIL_DELIVERY_CONNECTION_MESSAGE,
    EMAIL_DELIVERY_GENERIC_MESSAGE,
    EMAIL_DELIVERY_SECURITY_MESSAGE,
    EmailDeliveryError,
    EmailRecipientError,
    email_peer_configuration,
    get_email_status,
    parse_smtp_configuration,
    send_configuration_email,
    send_test_email,
    validate_recipient,
)
from api_app.mcp_tools import MCPToolError, WireGuardMCPToolset
from api_app.models import Peer, ServerConfiguration

SMTP_ENVIRONMENT = {
    "EMAIL_HOST": "smtp.gmail.com", "EMAIL_HOST_USER": "sender@gmail.com",
    "EMAIL_HOST_PASSWORD": "secret", "EMAIL_PORT": "587",
    "EMAIL_DEFAULT_FROM_EMAIL": "sender@gmail.com",
    "EMAIL_USE_TLS": "true", "EMAIL_USE_SSL": "false",
}

LOCAL_SMTP_ENVIRONMENT = {
    "EMAIL_HOST": "mail.local",
    "EMAIL_PORT": "25",
    "EMAIL_DEFAULT_FROM_EMAIL": "wg-ui-plus@mail.local",
}


class SMTPConfigurationTests(SimpleTestCase):
    def valid_environment(self):
        return {
            "EMAIL_HOST": "smtp.gmail.com",
            "EMAIL_HOST_USER": "sender@gmail.com",
            "EMAIL_HOST_PASSWORD": "secret",
            "EMAIL_PORT": "587",
            "EMAIL_DEFAULT_FROM_EMAIL": "sender@gmail.com",
            "EMAIL_USE_TLS": "True",
            "EMAIL_USE_SSL": "False",
        }

    def test_authenticated_configuration_is_typed(self):
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

    def test_disabled_security_modes_are_valid(self):
        configuration = parse_smtp_configuration(LOCAL_SMTP_ENVIRONMENT)
        self.assertEqual("mail.local", configuration.host)
        self.assertEqual(25, configuration.port)
        self.assertEqual("wg-ui-plus@mail.local", configuration.from_email)
        self.assertEqual("", configuration.username)
        self.assertEqual("", configuration.password)
        self.assertFalse(configuration.use_tls)
        self.assertFalse(configuration.use_ssl)

    def test_partial_credentials_in_either_direction_are_rejected(self):
        username_only = dict(LOCAL_SMTP_ENVIRONMENT, EMAIL_HOST_USER="sender@mail.local")
        password_only = dict(LOCAL_SMTP_ENVIRONMENT, EMAIL_HOST_PASSWORD="secret")
        with self.assertRaises(ImproperlyConfigured):
            parse_smtp_configuration(username_only)
        with self.assertRaises(ImproperlyConfigured):
            parse_smtp_configuration(password_only)

    def test_invalid_sender_and_default_sender_are_rejected(self):
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
    @patch.dict("os.environ", SMTP_ENVIRONMENT, clear=True)
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

    def assert_safe_delivery_failure(self, backend_error, expected_message):
        with self.assertLogs("api_app.email_service", level="ERROR") as logs:
            with patch.dict("os.environ", SMTP_ENVIRONMENT, clear=True), \
                    patch("api_app.email_service.EmailMessage") as email_class:
                email_class.return_value.send.side_effect = backend_error
                with self.assertRaises(EmailDeliveryError) as raised:
                    send_configuration_email(
                        "subject", "body", "peer@gmail.com",
                        base64.b64encode(b"png"), "configuration",
                    )
        self.assertEqual(expected_message, str(raised.exception))
        self.assertIs(backend_error, raised.exception.__cause__)
        self.assertNotIn(str(backend_error), str(raised.exception))
        self.assertNotIn(str(backend_error), logs.output[0])
        self.assertEqual(type(backend_error).__name__, logs.records[0].exception_type)

    def test_authentication_failure_has_safe_categorized_message(self):
        self.assert_safe_delivery_failure(
            smtplib.SMTPAuthenticationError(535, b"provider secret response"),
            EMAIL_DELIVERY_AUTHENTICATION_MESSAGE,
        )

    def test_connection_failure_has_safe_categorized_message(self):
        self.assert_safe_delivery_failure(
            smtplib.SMTPConnectError(421, b"provider connection response"),
            EMAIL_DELIVERY_CONNECTION_MESSAGE,
        )

    def test_network_timeout_has_connection_message(self):
        self.assert_safe_delivery_failure(socket.timeout("private network detail"), EMAIL_DELIVERY_CONNECTION_MESSAGE)

    def test_tls_failure_has_safe_security_message(self):
        self.assert_safe_delivery_failure(ssl.SSLError("certificate provider detail"), EMAIL_DELIVERY_SECURITY_MESSAGE)

    def test_generic_smtp_failure_has_safe_message(self):
        self.assert_safe_delivery_failure(
            smtplib.SMTPException("raw provider response"),
            EMAIL_DELIVERY_GENERIC_MESSAGE,
        )

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend",
        EMAIL_HOST="mail.local", EMAIL_PORT=25,
        EMAIL_HOST_USER="", EMAIL_HOST_PASSWORD="",
        EMAIL_USE_TLS=False, EMAIL_USE_SSL=False,
        DEFAULT_FROM_EMAIL="wg-ui-plus@mail.local",
    )
    @patch.dict("os.environ", LOCAL_SMTP_ENVIRONMENT, clear=True)
    @patch("django.core.mail.backends.smtp.smtplib.SMTP")
    def test_test_email_uses_smtp_boundary_without_auth(self, smtp_class):
        smtp_class.return_value.sendmail.return_value = {}
        send_test_email()
        smtp_connection = smtp_class.return_value
        smtp_connection.login.assert_not_called()
        smtp_connection.sendmail.assert_called_once()
        sender, recipients, mime_message = smtp_connection.sendmail.call_args.args
        mime_message = mime_message.decode() if isinstance(mime_message, bytes) else mime_message
        self.assertEqual("wg-ui-plus@mail.local", sender)
        self.assertEqual(["wg-ui-plus@mail.local"], recipients)
        self.assertIn("Subject: wg-ui-plus SMTP test email", mime_message)
        self.assertIn("This is a test email from wg-ui-plus.", mime_message)
        self.assertNotIn("Content-Disposition: attachment", mime_message)


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
        "EMAIL_DEFAULT_FROM_EMAIL": "sender@gmail.com",
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

    @patch("api_app.views.email_peer_configuration")
    def test_endpoint_returns_safe_classified_delivery_message(self, send):
        send.side_effect = EmailDeliveryError(EMAIL_DELIVERY_AUTHENTICATION_MESSAGE)
        response = self.client.post("/api/v1/data/peer/send_peer_email",
                                    {"peer_id": self.peer.id}, format="json")
        self.assertEqual(502, response.status_code)
        self.assertEqual(EMAIL_DELIVERY_AUTHENTICATION_MESSAGE, response.data["message"])

    def test_test_email_endpoint_requires_authentication(self):
        response = APIClient().post("/api/v1/control/send_test_email", {}, format="json")
        self.assertEqual(403, response.status_code)

    @patch.dict("os.environ", LOCAL_SMTP_ENVIRONMENT, clear=True)
    @patch("api_app.email_service.EmailMessage")
    def test_test_email_endpoint_delivers_configured_message_without_auth(self, email_class):
        response = self.client.post("/api/v1/control/send_test_email", {}, format="json")
        self.assertEqual(200, response.status_code)
        email_class.assert_called_once_with(
            subject="wg-ui-plus SMTP test email",
            body="This is a test email from wg-ui-plus.",
            from_email="wg-ui-plus@mail.local",
            to=["wg-ui-plus@mail.local"],
        )
        email_class.return_value.attach.assert_not_called()
        email_class.return_value.send.assert_called_once_with(fail_silently=False)

    @patch("api_app.views.deliver_test_email")
    def test_test_email_endpoint_returns_safe_failure(self, send):
        send.side_effect = EmailDeliveryError(EMAIL_DELIVERY_CONNECTION_MESSAGE)
        response = self.client.post("/api/v1/control/send_test_email", {}, format="json")
        self.assertEqual(502, response.status_code)
        self.assertEqual(EMAIL_DELIVERY_CONNECTION_MESSAGE, response.data["message"])

    @patch("api_app.views.deliver_test_email")
    def test_test_email_endpoint_rejects_recipient_override(self, send):
        response = self.client.post(
            "/api/v1/control/send_test_email",
            {"to": "attacker@example.com"}, format="json",
        )
        self.assertEqual(400, response.status_code)
        send.assert_not_called()

    @patch("api_app.email_service.send_configuration_email")
    @patch("api_app.serializers.PeerWithQrSerializer")
    @patch.dict("os.environ", {
        "EMAIL_HOST": "smtp.gmail.com", "EMAIL_HOST_USER": "sender@gmail.com",
        "EMAIL_HOST_PASSWORD": "secret", "EMAIL_PORT": "587",
        "EMAIL_DEFAULT_FROM_EMAIL": "sender@gmail.com",
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
    def test_mcp_delivery_failure_returns_safe_categorized_message(self, send):
        send.side_effect = EmailDeliveryError(EMAIL_DELIVERY_AUTHENTICATION_MESSAGE)
        with self.assertRaises(MCPToolError) as raised:
            WireGuardMCPToolset().send_peer_configuration_email(self.peer.id)
        self.assertEqual(EMAIL_DELIVERY_AUTHENTICATION_MESSAGE, str(raised.exception))
        self.assertNotIn("provider authentication response", str(raised.exception))

    @patch("api_app.mcp_tools.email_peer_configuration")
    def test_mcp_uses_saved_peer_and_rejects_override_argument(self, send):
        result = WireGuardMCPToolset().send_peer_configuration_email(self.peer.id)
        self.assertEqual("Email sent successfully!", result["message"])
        send.assert_called_once_with(self.peer)
        with self.assertRaises(TypeError):
            WireGuardMCPToolset().send_peer_configuration_email(
                self.peer.id, "attacker@example.com"
            )
