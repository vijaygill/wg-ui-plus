from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views
from .views import (PeerGroupViewSet, PeerViewSet, ServerConfigurationViewSet,
                    TargetHeirarchyViewSet, TargetViewSet)

router = DefaultRouter()
router.register(r"peer", PeerViewSet)
router.register(r"peer_group", PeerGroupViewSet)
router.register(r"target", TargetViewSet)
router.register(r"server_configuration", ServerConfigurationViewSet)
router.register(r"target_heirarchy", TargetHeirarchyViewSet, "target_heirarchy")

urlpatterns = [
    path("api/v1/data/", include(router.urls)),
    path("test/", views.test, name="test"),
    path(
        "api/v1/license",
        views.get_license,
        name="get_license",
    ),
    path(
        "api/v1/control/wireguard_generate_configuration_files",
        views.wireguard_generate_configuration_files,
        name="wireguard_generate_configuration_files",
    ),
    path(
        "api/v1/control/wireguard_restart",
        views.wireguard_restart,
        name="wireguard_restart",
    ),
    path(
        "api/v1/control/wireguard_get_configuration",
        views.wireguard_get_configuration,
        name="wireguard_get_configuration",
    ),
    path(
        "api/v1/control/wireguard_get_connected_peers",
        views.wireguard_get_connected_peers,
        name="wireguard_get_connected_peers",
    ),
    path(
        "api/v1/control/get_iptables_log",
        views.wireguard_get_iptables_log,
        name="wireguard_get_iptables_log",
    ),
    path(
        "api/v1/auth/login",
        views.auth_login,
        name="login",
    ),
    path(
        "api/v1/auth/logout",
        views.auth_logout,
        name="logout",
    ),
    path(
        "api/v1/auth/change_password",
        views.auth_change_password,
        name="change_password",
    ),
    path(
        "api/v1/control/get_server_status",
        views.get_server_status,
        name="get_server_status",
    ),
    path(
        "api/v1/data/peer/send_peer_email",
        views.send_peer_email,
        name="send_peer_email",
    ),
    path(
        "api/v1/control/send_test_email",
        views.send_test_email,
        name="send_test_email",
    ),
    path(
        "api/v1/control/mcp/configuration",
        views.MCPConfigurationView.as_view(),
        name="mcp_configuration",
    ),
    path(
        "api/v1/control/mcp/token",
        views.MCPTokenView.as_view(),
        name="mcp_token",
    ),
    path(
        "api/v1/control/email/configuration",
        views.EmailConfigurationView.as_view(),
        name="email_configuration",
    ),
    path(
        "api/v1/control/email/test_connectivity",
        views.test_email_connectivity,
        name="test_email_connectivity",
    ),
]
