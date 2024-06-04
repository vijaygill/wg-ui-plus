from io import BytesIO
import base64
import logging
import qrcode
from rest_framework import serializers
from rest_framework import permissions
from .models import Peer, PeerGroup, Target, ServerConfiguration
from .wireguardhelper import WireGuardHelper
from .db_seed import PEER_GROUP_EVERYONE_NAME

logger = logging.getLogger(__name__)


class PeerSerializer(serializers.ModelSerializer):
    target_names = serializers.SerializerMethodField(
        "get_target_names",
        read_only=True,
    )

    class Meta:
        model = Peer
        fields = "__all__"
        depth = 1

    def get_target_names(self, instance):
        res = []
        for peer_group in [x for x in instance.peer_groups.all() if not x.disabled]:
            for target in peer_group.targets.all():
                res += [(target, peer_group)]

        peer_group_everyone = PeerGroup.objects.filter(name=PEER_GROUP_EVERYONE_NAME)[0]
        if peer_group_everyone:
            for target in peer_group_everyone.targets.all():
                res += [(target, peer_group_everyone)]

        res = [f"{x[0].name}" for x in res]
        res = list(set(res))
        res.sort()
        res = ", ".join(res)
        return res


class PeerWithQrSerializer(serializers.ModelSerializer):
    peer_group_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=False,
        queryset=PeerGroup.objects.all(),
        source="peer_groups",
    )
    qr = serializers.SerializerMethodField(
        "get_qr",
        read_only=True,
    )
    configuration = serializers.SerializerMethodField(
        "get_configuration",
        read_only=True,
    )

    class Meta:
        model = Peer
        fields = "__all__"
        depth = 1

    def get_configuration(self, instance):
        wg = WireGuardHelper()
        serverConfiguration = ServerConfiguration.objects.all()[0]
        peer = instance
        s, c = wg.getWireguardConfigurationsForPeer(serverConfiguration, peer)
        if c:
            c = c.strip()
        return c

    def get_qr(self, instance):
        c = self.get_configuration(instance=instance)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=5,
        )
        qr.add_data(c)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        bytes_stream = BytesIO()
        img.save(bytes_stream, "PNG")
        bytes_stream.seek(0)
        res = base64.b64encode(bytes_stream.getvalue())
        return res


class PeerGroupSerializer(serializers.ModelSerializer):
    peer_ids = serializers.PrimaryKeyRelatedField(
        many=True, read_only=False, queryset=Peer.objects.all(), source="peers"
    )
    target_ids = serializers.PrimaryKeyRelatedField(
        many=True, read_only=False, queryset=Target.objects.all(), source="targets"
    )
    target_names = serializers.SerializerMethodField(
        "get_target_names",
        read_only=True,
    )
    is_everyone_group = serializers.SerializerMethodField(
        "get_is_everyone_group",
        read_only=True,
    )

    class Meta:
        model = PeerGroup
        fields = "__all__"
        depth = 1

    def get_target_names(self, instance):
        res = [f"{x.name}" for x in instance.targets.all()]
        res = list(set(res))
        res.sort()
        res = ", ".join(res)
        return res

    def get_is_everyone_group(self, instance):
        res = instance.name == PEER_GROUP_EVERYONE_NAME
        return res


class TargetHeirarchySerializer(serializers.ModelSerializer):
    class Meta:
        model = Target
        fields = "__all__"
        depth = 2


class TargetSerializer(serializers.ModelSerializer):
    peer_group_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=False,
        queryset=PeerGroup.objects.all(),
        source="peer_groups",
    )

    class Meta:
        model = Target
        fields = "__all__"
        depth = 1


class ServerConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServerConfiguration
        fields = "__all__"
        depth = 1
