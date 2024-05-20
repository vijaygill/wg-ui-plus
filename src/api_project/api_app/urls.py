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
    path('api/v1/', include(router.urls)),
]