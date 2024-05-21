from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.urls import path,include,re_path

from . import views

from .views import TargetViewSet, PeerGroupViewSet, PeerViewSet, ServerConfigurationViewSet

router = DefaultRouter()
router.register(r'peer', PeerViewSet)
router.register(r'peer_group', PeerGroupViewSet)
router.register(r'target', TargetViewSet)
router.register(r'server_configuration', ServerConfigurationViewSet)

urlpatterns = [
    path('api/v1/data/', include(router.urls)),
    path('test/', views.test, name='test'),
    path('api/v1/control/wireguard_generate_configuration_files', views.wireguard_generate_configuration_files, name='wireguard_generate_configuration_files'),
    path('api/v1/control/wireguard_restart', views.wireguard_restart, name='wireguard_restart'),
    path('api/v1/control/wireguard_get_configuration', views.wireguard_get_configuration, name='wireguard_get_configuration'),
]