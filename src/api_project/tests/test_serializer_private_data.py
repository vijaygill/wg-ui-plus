from datetime import datetime, timezone

from django.test import TestCase

from api_app.common import PEER_GROUP_EVERYONE_NAME
from api_app.models import Peer, PeerGroup, ServerConfiguration
from api_app.serializers import (
    PeerSerializer,
    PeerWithQrSerializer,
    ServerConfigurationSerializer,
)


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


class PeerSerializerPrivateDataTests(TestCase):
    def setUp(self):
        self.configuration = make_configuration()
        PeerGroup.objects.create(name=PEER_GROUP_EVERYONE_NAME)
        self.peer = Peer.objects.create(
            name="Laptop",
            description="test",
            private_key="peer-private-key",
            public_key="peer-public-key",
            ip_address="192.168.2.2",
            port=1196,
        )

    def test_peer_serializer_omits_private_key(self):
        data = PeerSerializer(instance=self.peer).data
        self.assertNotIn("private_key", data)
        self.assertNotIn("peer-private-key", str(data))
        self.assertEqual("peer-public-key", data["public_key"])
        self.assertEqual("Laptop", data["name"])

    def test_peer_with_qr_serializer_omits_private_key_but_keeps_configuration(self):
        data = PeerWithQrSerializer(instance=self.peer).data
        self.assertNotIn("private_key", data)
        fields = {key: value for key, value in data.items() if key != "configuration"}
        self.assertNotIn("peer-private-key", str(fields))
        self.assertIn("[Interface]", data["configuration"])
        self.assertIn("peer-private-key", data["configuration"])


class ServerConfigurationSerializerPrivateDataTests(TestCase):
    def setUp(self):
        self.configuration = make_configuration(
            private_key="server-private-key",
            public_key="server-public-key",
        )

    def test_server_configuration_serializer_omits_both_keys(self):
        data = ServerConfigurationSerializer(instance=self.configuration).data
        self.assertNotIn("private_key", data)
        self.assertNotIn("public_key", data)

    def test_partial_update_without_keys_preserves_stored_keys(self):
        serializer = ServerConfigurationSerializer(
            instance=self.configuration,
            data={"host_name_external": "renamed.example.test"},
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        self.configuration.refresh_from_db()
        self.assertEqual("server-private-key", self.configuration.private_key)
        self.assertEqual("server-public-key", self.configuration.public_key)
        self.assertEqual("renamed.example.test", self.configuration.host_name_external)
