from io import BytesIO
import base64
import logging
import qrcode
from rest_framework import serializers 
from .models import Peer, PeerGroup, Target, ServerConfiguration
from .wireguardhelper import WireGuardHelper

logger = logging.getLogger(__name__)

class PeerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Peer
        fields = '__all__'
        depth = 1

class PeerWithQrSerializer(serializers.ModelSerializer):
    peer_group_ids = serializers.PrimaryKeyRelatedField(many=True, read_only=False, queryset=PeerGroup.objects.all(), source='peer_groups')
    qr = serializers.SerializerMethodField('get_qr')
    configuration = serializers.SerializerMethodField('get_configuration')

    class Meta:
        model = Peer
        fields = '__all__'
        depth = 1

    def get_configuration(self, instance):
        wg = WireGuardHelper()
        serverConfiguration = ServerConfiguration.objects.all()[0]
        peer = instance
        s,c = wg.getWireguardConfigurationsForPeer(serverConfiguration, peer)
        return c

    def get_qr(self, instance):
        c = self.get_configuration(instance=instance)
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=5)
        qr.add_data(c)
        qr.make(fit = True)
        img = qr.make_image(fill_color="black", back_color="white")
        bytes_stream = BytesIO()
        img.save(bytes_stream, 'PNG')
        bytes_stream.seek(0)
        res = base64.b64encode(bytes_stream.getvalue())
        return res

class PeerGroupSerializer(serializers.ModelSerializer):
    peer_ids = serializers.PrimaryKeyRelatedField(many=True, read_only=False, queryset=Peer.objects.all(), source='peers')
    target_ids = serializers.PrimaryKeyRelatedField(many=True, read_only=False, queryset=Target.objects.all(), source='targets')
    class Meta:
       model = PeerGroup
       fields = '__all__'
       depth = 1

class TargetSerializer(serializers.ModelSerializer):
    peer_group_ids = serializers.PrimaryKeyRelatedField(many=True, read_only=False, queryset=PeerGroup.objects.all(), source='peer_groups')
    class Meta:
        model = Target
        fields = '__all__'
        depth = 1

class ServerConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServerConfiguration
        fields = '__all__'
        depth = 1

