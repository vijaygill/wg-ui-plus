"""Permission tests for the WireGuard configuration endpoint (REV-49)."""

from datetime import datetime, timezone

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from api_app.models import ServerConfiguration


class WireGuardConfigurationPermissionTests(TestCase):
    URL = "/api/v1/control/wireguard_get_configuration"

    def setUp(self):
        self.user = get_user_model().objects.create_user("admin", password="password")
        self.configuration = ServerConfiguration.objects.create(
            network_address="192.168.2.0/24",
            ip_address="192.168.2.1",
            host_name_external="vpn.example.test",
            port_external=1196,
            port_internal=51820,
            upstream_dns_ip_address="192.168.0.5",
            wireguard_config_path="/config/wireguard/wg0.conf",
            script_path_post_down="/config/post-down.sh",
            script_path_post_up="/config/post-up.sh",
            peer_default_port=1196,
            last_changed_datetime=datetime.now(timezone.utc),
        )
        self.assertTrue(
            self.configuration.private_key,
            "a missing server private key would make these assertions vacuous",
        )

    def test_anonymous_get_is_refused_and_does_not_expose_the_private_key(self):
        response = APIClient().get(self.URL)
        self.assertIn(response.status_code, (401, 403))
        self.assertNotEqual(200, response.status_code)
        body = response.content.decode()
        self.assertNotIn("PrivateKey", body)
        self.assertNotIn(self.configuration.private_key, body)

    def test_authenticated_get_returns_the_configuration(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.get(self.URL)
        self.assertEqual(200, response.status_code)
        self.assertIn(
            "server_configuration",
            response.data,
            "the payload shape changed, so the leak assertion above is no longer meaningful",
        )
        self.assertIn(self.configuration.private_key, response.data["server_configuration"])
