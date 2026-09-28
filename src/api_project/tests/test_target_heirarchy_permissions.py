"""Permission and projection tests for the target hierarchy surface (CR-14)."""

import json
from datetime import datetime, timezone

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from api_app.mcp_tools import WireGuardMCPToolset
from api_app.models import Peer, PeerGroup, ServerConfiguration, Target


def collect_nested_keys(value):
    """Recursively collect every dictionary key found at any nesting depth."""
    keys = set()
    if isinstance(value, dict):
        for key, item in value.items():
            keys.add(key)
            keys |= collect_nested_keys(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            keys |= collect_nested_keys(item)
    return keys


class TargetHeirarchyViewSetPermissionTests(TestCase):
    LIST_URL = "/api/v1/data/target_heirarchy/"

    def setUp(self):
        self.user = get_user_model().objects.create_user("admin", password="password")
        self.target = Target.objects.create(
            name="original",
            description="original description",
            ip_address="192.168.10.5",
            port=443,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def _detail_url(self):
        return f"/api/v1/data/target_heirarchy/{self.target.id}/"

    def _valid_create_payload(self):
        return {
            "name": "new-target",
            "description": "created by test",
            "ip_address": "192.168.10.7",
            "port": 8443,
        }

    def test_anonymous_get_list_is_allowed(self):
        response = APIClient().get(self.LIST_URL)
        self.assertEqual(200, response.status_code)

    def test_anonymous_get_detail_is_allowed(self):
        response = APIClient().get(self._detail_url())
        self.assertEqual(200, response.status_code)

    def test_anonymous_post_is_rejected_and_creates_nothing(self):
        count_before = Target.objects.count()
        response = APIClient().post(
            self.LIST_URL, self._valid_create_payload(), format="json"
        )
        self.assertEqual(403, response.status_code)
        self.assertEqual(count_before, Target.objects.count())
        self.assertFalse(Target.objects.filter(name="new-target").exists())

    def test_anonymous_post_invalid_payload_is_rejected_by_permissions_not_validation(self):
        response = APIClient().post(self.LIST_URL, {"ip_address": "x"}, format="json")
        self.assertEqual(403, response.status_code)
        self.assertEqual(1, Target.objects.count())

    def test_anonymous_put_is_rejected_and_changes_nothing(self):
        before = Target.objects.get(pk=self.target.pk)
        payload = {
            "name": "renamed",
            "description": "updated description",
            "disabled": True,
            "ip_address": "192.168.10.9",
            "port": 9999,
            "allow_modify_self": False,
            "allow_modify_peer_groups": False,
        }
        response = APIClient().put(self._detail_url(), payload, format="json")
        self.assertEqual(403, response.status_code)
        self.target.refresh_from_db()
        self.assertEqual(before.name, self.target.name)
        self.assertEqual(before.description, self.target.description)
        self.assertEqual(before.disabled, self.target.disabled)
        self.assertEqual(before.ip_address, self.target.ip_address)
        self.assertEqual(before.port, self.target.port)
        self.assertEqual(before.allow_modify_self, self.target.allow_modify_self)
        self.assertEqual(
            before.allow_modify_peer_groups, self.target.allow_modify_peer_groups
        )
        self.assertEqual(before.last_changed_datetime, self.target.last_changed_datetime)

    def test_anonymous_patch_is_rejected_and_name_unchanged(self):
        response = APIClient().patch(self._detail_url(), {"name": "renamed"}, format="json")
        self.assertEqual(403, response.status_code)
        self.target.refresh_from_db()
        self.assertEqual("original", self.target.name)

    def test_anonymous_delete_is_rejected_and_target_survives(self):
        response = APIClient().delete(self._detail_url())
        self.assertEqual(403, response.status_code)
        self.assertTrue(Target.objects.filter(pk=self.target.pk).exists())

    def test_authenticated_post_is_rejected_as_method_not_allowed(self):
        count_before = Target.objects.count()
        response = self.client.post(
            self.LIST_URL, self._valid_create_payload(), format="json"
        )
        self.assertEqual(405, response.status_code)
        self.assertEqual(count_before, Target.objects.count())
        self.assertFalse(Target.objects.filter(name="new-target").exists())

    def test_authenticated_put_is_rejected_as_method_not_allowed(self):
        payload = {
            "name": "renamed",
            "description": "updated description",
            "disabled": True,
            "ip_address": "192.168.10.9",
            "port": 9999,
            "allow_modify_self": False,
            "allow_modify_peer_groups": False,
        }
        response = self.client.put(self._detail_url(), payload, format="json")
        self.assertEqual(405, response.status_code)
        self.target.refresh_from_db()
        self.assertEqual("original", self.target.name)
        self.assertEqual("original description", self.target.description)
        self.assertEqual("192.168.10.5", self.target.ip_address)
        self.assertEqual(443, self.target.port)

    def test_authenticated_patch_is_rejected_as_method_not_allowed(self):
        response = self.client.patch(self._detail_url(), {"name": "renamed"}, format="json")
        self.assertEqual(405, response.status_code)
        self.target.refresh_from_db()
        self.assertEqual("original", self.target.name)
        self.assertEqual("original description", self.target.description)
        self.assertEqual("192.168.10.5", self.target.ip_address)
        self.assertEqual(443, self.target.port)

    def test_authenticated_delete_is_rejected_as_method_not_allowed(self):
        response = self.client.delete(self._detail_url())
        self.assertEqual(405, response.status_code)
        self.assertTrue(Target.objects.filter(pk=self.target.pk).exists())


class TargetHeirarchyProjectionTests(TestCase):
    """The hierarchy read surface must remain a non-sensitive projection (CR-14)."""

    LIST_URL = "/api/v1/data/target_heirarchy/"
    SENSITIVE_KEYS = ("private_key", "public_key", "email_address")

    def setUp(self):
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
        self.target = Target.objects.create(
            name="original",
            description="original description",
            ip_address="192.168.10.5",
            port=443,
        )
        self.peer = Peer.objects.create(
            name="Laptop",
            description="test peer",
            email_address="peer@example.test",
            private_key="peer-private-key",
            public_key="peer-public-key",
            ip_address="192.168.2.2",
            port=1196,
        )
        self.peer_group = PeerGroup.objects.create(
            name="Operators", description="operations group"
        )
        self.peer_group.peers.add(self.peer)
        self.peer_group.targets.add(self.target)

    def _assert_no_sensitive_keys_or_values(self, data):
        self.assertTrue(data, "an empty hierarchy payload would make this scan vacuous")
        keys = collect_nested_keys(data)
        for key in self.SENSITIVE_KEYS:
            self.assertNotIn(key, keys)
        body = json.dumps(data, default=str)
        self.assertNotIn(self.peer.private_key, body)
        self.assertNotIn(self.peer.public_key, body)
        self.assertNotIn(self.peer.email_address, body)

    def test_anonymous_get_does_not_expose_peer_credentials_or_personal_data(self):
        response = APIClient().get(self.LIST_URL)
        self.assertEqual(200, response.status_code)
        self._assert_no_sensitive_keys_or_values(response.data)

    def test_anonymous_get_includes_the_fields_used_by_the_vpn_layout_page(self):
        response = APIClient().get(self.LIST_URL)
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))
        target_data = response.data[0]
        self.assertEqual(
            {
                "id",
                "name",
                "description",
                "disabled",
                "ip_address",
                "port",
                "peer_groups",
            },
            set(target_data),
        )
        self.assertEqual(1, len(target_data["peer_groups"]))
        group_data = target_data["peer_groups"][0]
        self.assertEqual(
            {"id", "name", "description", "disabled", "peers"},
            set(group_data),
        )
        self.assertEqual(1, len(group_data["peers"]))
        peer_data = group_data["peers"][0]
        self.assertEqual(
            {"id", "name", "description", "disabled", "ip_address"},
            set(peer_data),
        )

    def test_mcp_get_hierarchy_omits_peer_credentials_and_personal_data(self):
        tools = WireGuardMCPToolset()
        data = tools.get_hierarchy()
        self._assert_no_sensitive_keys_or_values(data)

    def test_mcp_credential_tools_still_return_credential_material(self):
        tools = WireGuardMCPToolset()
        configuration = tools.get_peer_configuration(self.peer.id)
        self.assertEqual(self.peer.id, configuration["peer_id"])
        self.assertTrue(configuration["configuration"])
        self.assertIn(self.peer.private_key, configuration["configuration"])
        qr = tools.get_peer_qr(self.peer.id)
        self.assertEqual(self.peer.id, qr["peer_id"])
        self.assertTrue(qr["qr"])
