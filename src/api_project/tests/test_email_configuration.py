"""Focused tests for database-backed email configuration (CR-5)."""

import io
import json
import socket
from datetime import datetime, timezone
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import management
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIClient

from api_app.email_service import (
    CONNECTIVITY_TIMEOUT_SECONDS,
    EMAIL_PASSWORD_SENTINEL,
    EMAIL_SETTINGS_FIELDS,
    EmailConfigurationError,
    EmailDeliveryError,
    _resolved_environment,
    check_smtp_connectivity,
    database_to_environment,
    email_settings_payload,
    environment_overrides,
    get_email_status,
    send_test_email,
)
from api_app.models import ServerConfiguration


def make_configuration(**overrides):
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


def save_email_fields(configuration, **overrides):
    values = {
        "email_host": "db-mail.local",
        "email_port": 2525,
        "email_host_user": "",
        "email_host_password": None,
        "email_default_from_email": "db-sender@mail.local",
        "email_use_tls": False,
        "email_use_ssl": False,
    }
    values.update(overrides)
    for field, value in values.items():
        setattr(configuration, field, value)
    configuration.save(update_fields=list(values.keys()))
    return values


class EmailEnvironmentOverridesTests(SimpleTestCase):
    def test_mapping_covers_all_seven_fields(self):
        self.assertEqual(
            {
                "email_host": "EMAIL_HOST",
                "email_port": "EMAIL_PORT",
                "email_host_user": "EMAIL_HOST_USER",
                "email_host_password": "EMAIL_HOST_PASSWORD",
                "email_default_from_email": "EMAIL_DEFAULT_FROM_EMAIL",
                "email_use_tls": "EMAIL_USE_TLS",
                "email_use_ssl": "EMAIL_USE_SSL",
            },
            EMAIL_SETTINGS_FIELDS,
        )

    def test_string_fields_use_non_empty_presence(self):
        with patch.dict("os.environ", {"EMAIL_HOST": "mail.local", "EMAIL_PORT": ""}, clear=True):
            self.assertEqual({"email_host": "EMAIL_HOST"}, environment_overrides())

    def test_boolean_fields_count_as_set_only_when_true(self):
        with patch.dict("os.environ", {"EMAIL_USE_TLS": "False"}, clear=True):
            self.assertEqual({}, environment_overrides())
        with patch.dict("os.environ", {"EMAIL_USE_SSL": "false"}, clear=True):
            self.assertEqual({}, environment_overrides())
        with patch.dict("os.environ", {"EMAIL_USE_TLS": "True"}, clear=True):
            self.assertEqual({"email_use_tls": "EMAIL_USE_TLS"}, environment_overrides())
        with patch.dict("os.environ", {"EMAIL_USE_SSL": "1"}, clear=True):
            self.assertEqual({"email_use_ssl": "EMAIL_USE_SSL"}, environment_overrides())
        with patch.dict("os.environ", {"EMAIL_USE_TLS": "on"}, clear=True):
            self.assertEqual({"email_use_tls": "EMAIL_USE_TLS"}, environment_overrides())

    def test_boolean_fields_with_unparseable_values_are_not_set(self):
        with patch.dict("os.environ", {"EMAIL_USE_TLS": "maybe"}, clear=True):
            self.assertEqual({}, environment_overrides())

    def test_missing_variables_produce_no_overrides(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual({}, environment_overrides())

    def test_database_to_environment_shapes_values_for_parser(self):
        configuration = type("Configuration", (), {
            "email_host": "mail.local", "email_port": 25, "email_host_user": "",
            "email_host_password": None, "email_default_from_email": "wg-ui-plus@mail.local",
            "email_use_tls": None, "email_use_ssl": False,
        })()
        environ = database_to_environment(configuration)
        self.assertEqual("mail.local", environ["EMAIL_HOST"])
        self.assertEqual("25", environ["EMAIL_PORT"])
        self.assertEqual("false", environ["EMAIL_USE_TLS"])
        self.assertEqual("", environ["EMAIL_HOST_PASSWORD"])


class EmailEffectiveConfigurationTests(TestCase):
    def setUp(self):
        self.configuration = make_configuration()

    @patch.dict("os.environ", {}, clear=True)
    def test_database_values_are_used_when_environment_absent(self):
        save_email_fields(self.configuration)
        status = get_email_status(configuration=self.configuration)
        self.assertEqual("configured", status["status"])

    @patch.dict("os.environ", {"EMAIL_USE_TLS": "False"}, clear=True)
    def test_partial_environment_merges_with_fully_configured_database(self):
        save_email_fields(self.configuration)
        status = get_email_status(configuration=self.configuration)
        self.assertEqual("configured", status["status"])
        merged = _resolved_environment(configuration=self.configuration)
        # The "False" value no longer counts as set, so EMAIL_USE_TLS comes
        # from the database; the rest is DB data too.
        self.assertEqual("false", merged["EMAIL_USE_TLS"])
        self.assertEqual("db-mail.local", merged["EMAIL_HOST"])
        self.assertEqual("2525", merged["EMAIL_PORT"])

    @patch.dict("os.environ", {"EMAIL_HOST": "env-mail.local"}, clear=True)
    def test_environment_overrides_only_the_present_field(self):
        save_email_fields(self.configuration)
        merged = _resolved_environment(configuration=self.configuration)
        self.assertEqual("env-mail.local", merged["EMAIL_HOST"])
        self.assertEqual("2525", merged["EMAIL_PORT"])
        self.assertEqual("db-sender@mail.local", merged["EMAIL_DEFAULT_FROM_EMAIL"])

    @patch.dict("os.environ", {}, clear=True)
    def test_unavailable_when_database_has_no_required_fields(self):
        status = get_email_status(configuration=self.configuration)
        self.assertEqual("unavailable", status["status"])

    @patch.dict("os.environ", {
        "EMAIL_HOST": "env-mail.local", "EMAIL_PORT": "not-a-port",
        "EMAIL_DEFAULT_FROM_EMAIL": "env-sender@mail.local",
    }, clear=True)
    def test_environment_wins_over_database(self):
        save_email_fields(self.configuration)
        status = get_email_status(configuration=self.configuration)
        self.assertEqual("invalid", status["status"])

    @patch.dict("os.environ", {}, clear=True)
    def test_payload_masks_password_and_reports_db_state(self):
        save_email_fields(
            self.configuration,
            email_host_user="db-user@mail.local",
            email_host_password="db-secret",
        )
        payload = email_settings_payload(self.configuration)
        self.assertTrue(payload["email_password_set"])
        self.assertNotIn("db-secret", json.dumps(payload))
        self.assertEqual("db-mail.local", payload["email_host"])
        self.assertEqual(2525, payload["email_port"])
        self.assertEqual({}, payload["environment_overrides"])
        self.assertEqual("configured", payload["effective"]["status"])

    @patch.dict("os.environ", {"EMAIL_USE_TLS": "False", "EMAIL_USE_SSL": "true"}, clear=True)
    def test_payload_effective_status_uses_merged_environment(self):
        save_email_fields(self.configuration)
        payload = email_settings_payload(self.configuration)
        self.assertEqual(
            {"email_use_ssl": "EMAIL_USE_SSL"},
            payload["environment_overrides"],
        )
        self.assertEqual("configured", payload["effective"]["status"])
        merged = _resolved_environment(configuration=self.configuration)
        self.assertEqual("false", merged["EMAIL_USE_TLS"])
        self.assertEqual("true", merged["EMAIL_USE_SSL"])

    @patch.dict("os.environ", {"EMAIL_HOST": "env-mail.local"}, clear=True)
    def test_payload_reports_environment_overrides(self):
        payload = email_settings_payload(self.configuration)
        self.assertEqual({"email_host": "EMAIL_HOST"}, payload["environment_overrides"])


class EmailConfigurationEndpointTests(TestCase):
    def setUp(self):
        self.configuration = make_configuration()
        self.user = get_user_model().objects.create_user("admin", password="password")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_get_requires_authentication(self):
        response = APIClient().get("/api/v1/control/email/configuration")
        self.assertEqual(403, response.status_code)

    @patch.dict("os.environ", {}, clear=True)
    def test_get_masks_password_and_never_returns_it(self):
        self.configuration.email_host = "mail.local"
        self.configuration.email_port = 25
        self.configuration.email_host_user = "sender@mail.local"
        self.configuration.email_host_password = "super-secret"
        self.configuration.email_default_from_email = "sender@mail.local"
        self.configuration.save(update_fields=[
            "email_host", "email_port", "email_host_user",
            "email_host_password", "email_default_from_email",
        ])
        response = self.client.get("/api/v1/control/email/configuration")
        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertTrue(payload["email_password_set"])
        self.assertNotIn("super-secret", response.content.decode())
        self.assertNotIn("email_host_password", response.content.decode())
        self.assertEqual({}, payload["environment_overrides"])
        self.assertEqual("configured", payload["effective"]["status"])

    @patch.dict("os.environ", {"EMAIL_HOST": "env-mail.local"}, clear=True)
    def test_get_reports_environment_overrides(self):
        response = self.client.get("/api/v1/control/email/configuration")
        self.assertEqual(200, response.status_code)
        self.assertEqual({"email_host": "EMAIL_HOST"}, response.json()["environment_overrides"])

    @patch.dict("os.environ", {}, clear=True)
    def test_patch_saves_values_and_keeps_password_on_blank(self):
        self.configuration.email_host = "old-mail.local"
        self.configuration.email_port = 25
        self.configuration.email_host_user = "user@mail.local"
        self.configuration.email_host_password = "stored-secret"
        self.configuration.email_default_from_email = "sender@mail.local"
        self.configuration.save(update_fields=[
            "email_host", "email_port", "email_host_user",
            "email_host_password", "email_default_from_email",
        ])
        response = self.client.patch("/api/v1/control/email/configuration", {
            "email_host": "new-mail.local",
            "email_port": "2525",
            "email_host_user": "new-user@mail.local",
            "email_host_password": "",
            "email_default_from_email": "new-sender@mail.local",
            "email_use_tls": True,
            "email_use_ssl": False,
        }, format="json")
        self.assertEqual(200, response.status_code)
        self.configuration.refresh_from_db()
        self.assertEqual("new-mail.local", self.configuration.email_host)
        self.assertEqual(2525, self.configuration.email_port)
        self.assertEqual("new-user@mail.local", self.configuration.email_host_user)
        self.assertEqual("stored-secret", self.configuration.email_host_password)
        self.assertEqual("new-sender@mail.local", self.configuration.email_default_from_email)
        self.assertTrue(self.configuration.email_use_tls)
        self.assertFalse(self.configuration.email_use_ssl)
        self.assertTrue(response.json()["email_password_set"])
        self.assertNotIn("stored-secret", response.content.decode())

    @patch.dict("os.environ", {}, clear=True)
    def test_patch_sentinel_keeps_stored_password(self):
        self.configuration.email_host_password = "stored-secret"
        self.configuration.save(update_fields=["email_host_password"])
        response = self.client.patch("/api/v1/control/email/configuration", {
            "email_host_password": EMAIL_PASSWORD_SENTINEL,
        }, format="json")
        self.assertEqual(200, response.status_code)
        self.configuration.refresh_from_db()
        self.assertEqual("stored-secret", self.configuration.email_host_password)

    @patch.dict("os.environ", {}, clear=True)
    def test_patch_new_password_replaces_stored_value(self):
        self.configuration.email_host_password = "stored-secret"
        self.configuration.save(update_fields=["email_host_password"])
        response = self.client.patch("/api/v1/control/email/configuration", {
            "email_host_password": "brand-new-secret",
        }, format="json")
        self.assertEqual(200, response.status_code)
        self.configuration.refresh_from_db()
        self.assertEqual("brand-new-secret", self.configuration.email_host_password)
        self.assertNotIn("brand-new-secret", response.content.decode())

    @patch.dict("os.environ", {"EMAIL_HOST": "env-mail.local"}, clear=True)
    def test_patch_rejects_environment_controlled_field(self):
        response = self.client.patch("/api/v1/control/email/configuration", {
            "email_host": "other-mail.local",
        }, format="json")
        self.assertEqual(400, response.status_code)
        self.assertIn("EMAIL_HOST", response.json()["email_host"][0])

    @patch.dict("os.environ", {"EMAIL_USE_TLS": "True"}, clear=True)
    def test_patch_rejects_environment_controlled_boolean_field(self):
        response = self.client.patch("/api/v1/control/email/configuration", {
            "email_use_tls": True,
        }, format="json")
        self.assertEqual(400, response.status_code)
        self.assertIn("EMAIL_USE_TLS", response.json()["email_use_tls"][0])

    @patch.dict("os.environ", {"EMAIL_USE_TLS": "False"}, clear=True)
    def test_patch_allows_changing_boolean_field_when_environment_value_is_false(self):
        response = self.client.patch("/api/v1/control/email/configuration", {
            "email_use_tls": True,
        }, format="json")
        self.assertEqual(200, response.status_code)
        self.configuration.refresh_from_db()
        self.assertTrue(self.configuration.email_use_tls)

    @patch.dict("os.environ", {"EMAIL_USE_TLS": "True"}, clear=True)
    def test_patch_full_payload_matching_database_is_accepted_with_environment_override(self):
        save_email_fields(
            self.configuration,
            email_host_user="db-user@mail.local",
            email_host_password="db-secret",
        )
        response = self.client.patch("/api/v1/control/email/configuration", {
            "email_host": "db-mail.local",
            "email_port": 2525,
            "email_host_user": "db-user@mail.local",
            "email_host_password": EMAIL_PASSWORD_SENTINEL,
            "email_default_from_email": "db-sender@mail.local",
            "email_use_tls": False,
            "email_use_ssl": False,
        }, format="json")
        self.assertEqual(200, response.status_code)
        self.configuration.refresh_from_db()
        self.assertEqual("db-mail.local", self.configuration.email_host)
        self.assertEqual(2525, self.configuration.email_port)
        self.assertEqual("db-user@mail.local", self.configuration.email_host_user)
        self.assertEqual("db-secret", self.configuration.email_host_password)
        self.assertEqual("db-sender@mail.local", self.configuration.email_default_from_email)
        self.assertFalse(self.configuration.email_use_tls)
        self.assertFalse(self.configuration.email_use_ssl)

    @patch.dict("os.environ", {}, clear=True)
    def test_patch_rejects_username_without_password(self):
        response = self.client.patch("/api/v1/control/email/configuration", {
            "email_host_user": "user@mail.local",
        }, format="json")
        self.assertEqual(400, response.status_code)
        self.assertIn("must be supplied together", response.json()["email_host_user"][0])

    @patch.dict("os.environ", {}, clear=True)
    def test_patch_rejects_clearing_username_while_password_exists(self):
        self.configuration.email_host_user = "user@mail.local"
        self.configuration.email_host_password = "stored-secret"
        self.configuration.save(update_fields=["email_host_user", "email_host_password"])
        response = self.client.patch("/api/v1/control/email/configuration", {
            "email_host_user": "",
        }, format="json")
        self.assertEqual(400, response.status_code)
        self.assertIn("must be supplied together", response.json()["email_host_user"][0])

    @patch.dict("os.environ", {}, clear=True)
    def test_patch_rejects_invalid_from_email_format(self):
        response = self.client.patch("/api/v1/control/email/configuration", {
            "email_default_from_email": "not-an-email",
        }, format="json")
        self.assertEqual(400, response.status_code)
        self.assertIn("valid email address", response.json()["email_default_from_email"][0])

    @patch.dict("os.environ", {}, clear=True)
    def test_patch_rejects_whitespace_only_host(self):
        response = self.client.patch("/api/v1/control/email/configuration", {
            "email_host": "   ",
        }, format="json")
        self.assertEqual(400, response.status_code)
        self.assertIn("non-empty host", response.json()["email_host"][0])

    @patch.dict("os.environ", {}, clear=True)
    def test_patch_accepts_null_port_to_clear_it(self):
        self.configuration.email_port = 25
        self.configuration.save(update_fields=["email_port"])
        response = self.client.patch("/api/v1/control/email/configuration", {
            "email_port": None,
        }, format="json")
        self.assertEqual(200, response.status_code)
        self.configuration.refresh_from_db()
        self.assertIsNone(self.configuration.email_port)

    @patch.dict("os.environ", {}, clear=True)
    def test_patch_rejects_port_out_of_range(self):
        response = self.client.patch("/api/v1/control/email/configuration", {
            "email_port": 70000,
        }, format="json")
        self.assertEqual(400, response.status_code)
        self.assertIn("between 1 and 65535", response.json()["email_port"][0])

    @patch.dict("os.environ", {}, clear=True)
    def test_patch_rejects_tls_and_ssl_together(self):
        response = self.client.patch("/api/v1/control/email/configuration", {
            "email_use_tls": True, "email_use_ssl": True,
        }, format="json")
        self.assertEqual(400, response.status_code)
        self.assertIn("cannot both be enabled", response.json()["email_use_tls"][0])

    @patch.dict("os.environ", {}, clear=True)
    def test_patch_rejects_non_boolean_security_modes(self):
        response = self.client.patch("/api/v1/control/email/configuration", {
            "email_use_tls": "true",
        }, format="json")
        self.assertEqual(400, response.status_code)
        self.assertIn("boolean", response.json()["email_use_tls"][0])

    @patch.dict("os.environ", {}, clear=True)
    def test_patch_rejects_unknown_fields(self):
        response = self.client.patch("/api/v1/control/email/configuration", {
            "email_password_set": True,
        }, format="json")
        self.assertEqual(400, response.status_code)
        self.assertIn("Unknown fields", response.json()["detail"][0])


class EmailStartupSeedingTests(TestCase):
    def setUp(self):
        self.configuration = make_configuration()

    @patch.dict("os.environ", {
        "EMAIL_HOST": "seed-mail.local",
        "EMAIL_PORT": "2525",
        "EMAIL_HOST_USER": "seed-user@mail.local",
        "EMAIL_HOST_PASSWORD": "seed-secret",
        "EMAIL_DEFAULT_FROM_EMAIL": "seed-sender@mail.local",
        "EMAIL_USE_TLS": "False",
        "EMAIL_USE_SSL": "true",
    }, clear=True)
    def test_startup_seeds_email_fields_from_environment(self):
        management.call_command("db_init_db_on_start", stdout=io.StringIO())
        self.configuration.refresh_from_db()
        self.assertEqual("seed-mail.local", self.configuration.email_host)
        self.assertEqual(2525, self.configuration.email_port)
        self.assertEqual("seed-user@mail.local", self.configuration.email_host_user)
        self.assertEqual("seed-secret", self.configuration.email_host_password)
        self.assertEqual("seed-sender@mail.local", self.configuration.email_default_from_email)
        self.assertFalse(self.configuration.email_use_tls)
        self.assertTrue(self.configuration.email_use_ssl)

    @patch.dict("os.environ", {
        "EMAIL_USE_TLS": "on",
        "EMAIL_USE_SSL": "off",
    }, clear=True)
    def test_startup_seeding_accepts_on_off_like_email_service(self):
        management.call_command("db_init_db_on_start", stdout=io.StringIO())
        self.configuration.refresh_from_db()
        self.assertTrue(self.configuration.email_use_tls)
        self.assertFalse(self.configuration.email_use_ssl)

    @patch.dict("os.environ", {"EMAIL_USE_TLS": "False"}, clear=True)
    def test_startup_seeding_keeps_database_boolean_when_environment_is_false(self):
        self.configuration.email_use_tls = True
        self.configuration.save(update_fields=["email_use_tls"])
        management.call_command("db_init_db_on_start", stdout=io.StringIO())
        self.configuration.refresh_from_db()
        self.assertTrue(self.configuration.email_use_tls)


class EmailSendPathTests(TestCase):
    def setUp(self):
        self.configuration = make_configuration()

    @patch.dict("os.environ", {}, clear=True)
    @patch("api_app.email_service.EmailBackend")
    @patch("api_app.email_service.EmailMessage")
    def test_send_uses_database_configuration_when_environment_absent(self, email_class, backend_class):
        save_email_fields(
            self.configuration,
            email_host_user="db-user@mail.local",
            email_host_password="db-secret",
            email_use_tls=True,
        )
        send_test_email()
        backend_class.assert_called_once_with(
            host="db-mail.local",
            port=2525,
            username="db-user@mail.local",
            password="db-secret",
            use_tls=True,
            use_ssl=False,
            fail_silently=False,
        )
        email_class.assert_called_once()
        self.assertIs(
            backend_class.return_value,
            email_class.call_args.kwargs["connection"],
        )
        email_class.return_value.send.assert_called_once_with(fail_silently=False)


class EmailConnectivityTests(TestCase):
    """TCP reachability check against the resolved SMTP host/port."""

    def setUp(self):
        self.configuration = make_configuration()

    @patch.dict("os.environ", {
        "EMAIL_HOST": "connectivity-mail.local",
        "EMAIL_PORT": "2525",
    }, clear=True)
    @patch("api_app.email_service.socket.create_connection")
    def test_success_opens_tcp_socket_to_resolved_host_and_port(self, create_connection):
        result = check_smtp_connectivity()
        create_connection.assert_called_once_with(
            ("connectivity-mail.local", 2525),
            timeout=CONNECTIVITY_TIMEOUT_SECONDS,
        )
        self.assertEqual(
            {"message": "SMTP server is reachable at connectivity-mail.local:2525."},
            result,
        )

    @patch.dict("os.environ", {}, clear=True)
    @patch("api_app.email_service.socket.create_connection")
    def test_uses_database_host_and_port_when_environment_absent(self, create_connection):
        save_email_fields(
            self.configuration,
            email_host="db-connectivity.local",
            email_port=2526,
        )
        check_smtp_connectivity()
        create_connection.assert_called_once_with(
            ("db-connectivity.local", 2526),
            timeout=CONNECTIVITY_TIMEOUT_SECONDS,
        )

    @patch.dict("os.environ", {"EMAIL_HOST": "env-host.local"}, clear=True)
    @patch("api_app.email_service.socket.create_connection")
    def test_environment_host_merges_with_database_port(self, create_connection):
        save_email_fields(self.configuration, email_port=2527)
        check_smtp_connectivity()
        create_connection.assert_called_once_with(
            ("env-host.local", 2527),
            timeout=CONNECTIVITY_TIMEOUT_SECONDS,
        )

    @patch.dict("os.environ", {}, clear=True)
    def test_missing_host_and_port_raise_configuration_error(self):
        with self.assertRaises(EmailConfigurationError) as ctx:
            check_smtp_connectivity()
        self.assertEqual(
            "SMTP email is not configured. Set EMAIL_HOST and EMAIL_PORT.",
            str(ctx.exception),
        )

    @patch.dict("os.environ", {"EMAIL_HOST": "connectivity-mail.local"}, clear=True)
    def test_missing_port_raises_configuration_error(self):
        with self.assertRaises(EmailConfigurationError) as ctx:
            check_smtp_connectivity()
        self.assertEqual(
            "SMTP email is not configured. Set EMAIL_HOST and EMAIL_PORT.",
            str(ctx.exception),
        )

    @patch.dict("os.environ", {
        "EMAIL_HOST": "connectivity-mail.local",
        "EMAIL_PORT": "not-a-number",
    }, clear=True)
    def test_non_integer_port_raises_configuration_error(self):
        with self.assertRaises(EmailConfigurationError) as ctx:
            check_smtp_connectivity()
        self.assertEqual(
            "SMTP email is not configured. Set EMAIL_HOST and EMAIL_PORT.",
            str(ctx.exception),
        )

    @patch.dict("os.environ", {
        "EMAIL_HOST": "connectivity-mail.local",
        "EMAIL_PORT": "70000",
    }, clear=True)
    def test_port_out_of_range_raises_configuration_error(self):
        with self.assertRaises(EmailConfigurationError) as ctx:
            check_smtp_connectivity()
        self.assertEqual(
            "SMTP email is not configured. Set EMAIL_HOST and EMAIL_PORT.",
            str(ctx.exception),
        )

    @patch.dict("os.environ", {
        "EMAIL_HOST": "connectivity-mail.local",
        "EMAIL_PORT": "25",
    }, clear=True)
    @patch(
        "api_app.email_service.socket.create_connection",
        side_effect=socket.gaierror("getaddrinfo failed"),
    )
    def test_unresolvable_host_raises_delivery_error(self, create_connection):
        with self.assertRaises(EmailDeliveryError) as ctx:
            check_smtp_connectivity()
        self.assertEqual(
            "The SMTP host name could not be resolved. Check EMAIL_HOST.",
            str(ctx.exception),
        )

    @patch.dict("os.environ", {
        "EMAIL_HOST": "connectivity-mail.local",
        "EMAIL_PORT": "25",
    }, clear=True)
    @patch(
        "api_app.email_service.socket.create_connection",
        side_effect=socket.timeout(),
    )
    def test_timeout_raises_delivery_error(self, create_connection):
        with self.assertRaises(EmailDeliveryError) as ctx:
            check_smtp_connectivity()
        self.assertEqual(
            "The SMTP server did not respond. Check the host and port, and that "
            "the port is reachable from the container (for Docker, check the "
            "port mapping).",
            str(ctx.exception),
        )

    @patch.dict("os.environ", {
        "EMAIL_HOST": "connectivity-mail.local",
        "EMAIL_PORT": "25",
    }, clear=True)
    @patch(
        "api_app.email_service.socket.create_connection",
        side_effect=ConnectionRefusedError(),
    )
    def test_refused_connection_raises_delivery_error(self, create_connection):
        with self.assertRaises(EmailDeliveryError) as ctx:
            check_smtp_connectivity()
        self.assertEqual(
            "The connection to the SMTP server was refused. Check the host, "
            "port, and firewall or Docker port mapping.",
            str(ctx.exception),
        )


class EmailConnectivityEndpointTests(TestCase):
    def setUp(self):
        self.configuration = make_configuration()
        self.user = get_user_model().objects.create_user("admin", password="password")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_requires_authentication(self):
        response = APIClient().post(
            "/api/v1/control/email/test_connectivity", {}, format="json"
        )
        self.assertEqual(403, response.status_code)

    @patch.dict("os.environ", {
        "EMAIL_HOST": "connectivity-mail.local",
        "EMAIL_PORT": "2525",
    }, clear=True)
    @patch("api_app.email_service.socket.create_connection")
    def test_reports_reachable_server(self, create_connection):
        response = self.client.post(
            "/api/v1/control/email/test_connectivity", {}, format="json"
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            "SMTP server is reachable at connectivity-mail.local:2525.",
            response.json()["message"],
        )

    @patch.dict("os.environ", {
        "EMAIL_HOST": "connectivity-mail.local",
        "EMAIL_PORT": "2525",
    }, clear=True)
    @patch(
        "api_app.email_service.socket.create_connection",
        side_effect=socket.timeout(),
    )
    def test_timeout_returns_safe_message_with_502(self, create_connection):
        response = self.client.post(
            "/api/v1/control/email/test_connectivity", {}, format="json"
        )
        self.assertEqual(502, response.status_code)
        self.assertEqual(
            "The SMTP server did not respond. Check the host and port, and that "
            "the port is reachable from the container (for Docker, check the "
            "port mapping).",
            response.json()["message"],
        )

    @patch.dict("os.environ", {
        "EMAIL_HOST": "connectivity-mail.local",
        "EMAIL_PORT": "2525",
    }, clear=True)
    @patch(
        "api_app.email_service.socket.create_connection",
        side_effect=socket.gaierror("name or service not known"),
    )
    def test_unresolvable_host_returns_safe_message_with_502(self, create_connection):
        response = self.client.post(
            "/api/v1/control/email/test_connectivity", {}, format="json"
        )
        self.assertEqual(502, response.status_code)
        self.assertEqual(
            "The SMTP host name could not be resolved. Check EMAIL_HOST.",
            response.json()["message"],
        )

    @patch.dict("os.environ", {
        "EMAIL_HOST": "connectivity-mail.local",
        "EMAIL_PORT": "2525",
    }, clear=True)
    @patch(
        "api_app.email_service.socket.create_connection",
        side_effect=ConnectionRefusedError(),
    )
    def test_refused_connection_returns_safe_message_with_502(self, create_connection):
        response = self.client.post(
            "/api/v1/control/email/test_connectivity", {}, format="json"
        )
        self.assertEqual(502, response.status_code)
        self.assertEqual(
            "The connection to the SMTP server was refused. Check the host, "
            "port, and firewall or Docker port mapping.",
            response.json()["message"],
        )

    @patch.dict("os.environ", {}, clear=True)
    def test_missing_configuration_returns_503(self):
        response = self.client.post(
            "/api/v1/control/email/test_connectivity", {}, format="json"
        )
        self.assertEqual(503, response.status_code)
        self.assertEqual(
            "SMTP email is not configured. Set EMAIL_HOST and EMAIL_PORT.",
            response.json()["message"],
        )

    @patch.dict("os.environ", {"EMAIL_HOST": "connectivity-mail.local"}, clear=True)
    def test_non_integer_port_returns_503(self):
        response = self.client.post(
            "/api/v1/control/email/test_connectivity", {}, format="json"
        )
        self.assertEqual(503, response.status_code)
        self.assertEqual(
            "SMTP email is not configured. Set EMAIL_HOST and EMAIL_PORT.",
            response.json()["message"],
        )

    @patch.dict("os.environ", {
        "EMAIL_HOST": "connectivity-mail.local",
        "EMAIL_PORT": "70000",
    }, clear=True)
    def test_port_out_of_range_returns_503(self):
        response = self.client.post(
            "/api/v1/control/email/test_connectivity", {}, format="json"
        )
        self.assertEqual(503, response.status_code)
        self.assertEqual(
            "SMTP email is not configured. Set EMAIL_HOST and EMAIL_PORT.",
            response.json()["message"],
        )

    @patch.dict("os.environ", {
        "EMAIL_HOST": "connectivity-mail.local",
        "EMAIL_PORT": "2525",
    }, clear=True)
    def test_request_body_is_rejected(self):
        response = self.client.post(
            "/api/v1/control/email/test_connectivity",
            {"host": "other-mail.local"},
            format="json",
        )
        self.assertEqual(400, response.status_code)

    @patch.dict("os.environ", {
        "EMAIL_HOST": "connectivity-mail.local",
        "EMAIL_PORT": "2525",
    }, clear=True)
    @patch(
        "api_app.views.check_smtp_connectivity",
        side_effect=RuntimeError("boom: raw detail"),
    )
    def test_unexpected_failure_returns_curated_500_without_internal_detail(self, check_connectivity):
        response = self.client.post(
            "/api/v1/control/email/test_connectivity", {}, format="json"
        )
        self.assertEqual(500, response.status_code)
        self.assertEqual(
            "The SMTP server could not be checked. Check the server logs for more details.",
            response.json()["message"],
        )
        self.assertNotIn("boom", response.content.decode())


class ServerConfigurationSerializerEmailTests(TestCase):
    def setUp(self):
        self.configuration = make_configuration()
        self.user = get_user_model().objects.create_user("admin", password="password")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch.dict("os.environ", {}, clear=True)
    def test_email_fields_are_not_exposed_through_server_configuration_api(self):
        self.configuration.email_host = "mail.local"
        self.configuration.email_port = 25
        self.configuration.email_host_user = "user@mail.local"
        self.configuration.email_host_password = "never-leak"
        self.configuration.email_default_from_email = "sender@mail.local"
        self.configuration.save(update_fields=[
            "email_host", "email_port", "email_host_user", "email_host_password",
            "email_default_from_email",
        ])
        response = self.client.get("/api/v1/data/server_configuration/")
        self.assertEqual(200, response.status_code)
        self.assertNotIn("never-leak", response.content.decode())
        for field in (
            "email_host", "email_port", "email_host_user", "email_host_password",
            "email_default_from_email", "email_use_tls", "email_use_ssl",
        ):
            self.assertNotIn(field, response.json()[0])
