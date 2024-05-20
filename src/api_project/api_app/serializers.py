from rest_framework import serializers 
from .models import Peer, PeerGroup, Target, ServerConfiguration

class PeerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Peer
        fields = '__all__'
        depth = 1

class PeerGroupSerializer(serializers.ModelSerializer):
    class Meta:
       model = PeerGroup
       fields = '__all__'
       depth = 1

class TargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Target
        fields = '__all__'
        depth = 1

class ServerConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServerConfiguration
        fields = '__all__'
        depth = 1

