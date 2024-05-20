from rest_framework import serializers 
from .models import Peer, PeerGroup, Target, ServerConfiguration

class PeerGroupSerializer1(serializers.ModelSerializer):
    class Meta:
       model = PeerGroup
       fields = ['id', 'name', 'description' ]

class PeerSerializer(serializers.ModelSerializer):
    peer_group_ids = serializers.PrimaryKeyRelatedField(many=True, read_only=False, queryset=PeerGroup.objects.all(), source='peer_groups')

    class Meta:
        model = Peer
        fields = '__all__'
        #fields = ['id', 'name', 'description','disabled','ip_address','port', 'pgs' ]
        depth = 1
    def update(self, instance, validated_data):
        print(f'>>>> validated_data: {validated_data}')
        return super(PeerSerializer, self).update(instance, validated_data)

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

