from django.contrib import admin

from .models import Peer, PeerGroup, Target, ServerConfiguration


class PeerAdmin(admin.ModelAdmin):

    def get_list_display(self, request):
        return ("name", "description", "ip_address", "disabled")

    def get_fields(self, request, obj=None):
        return ["name", "description", "disabled", "ip_address", "peer_groups"]

    def get_readonly_fields(self, request, obj=None):
        res = ["ip_address"]
        return res


class PeerGroupAdmin(admin.ModelAdmin):
    def get_list_display(self, request):
        return (
            "name",
            "description",
            "disabled",
        )

    def get_fields(self, request, obj=None):
        return ["name", "description", "disabled", "peers", "targets"]

    def get_readonly_fields(self, request, obj=None):
        res = []
        if obj:
            if not obj.allow_modify_self:
                res += ["name", "description", "disabled"]
            if not obj.allow_modify_peers:
                res += ["peers"]
            if not obj.allow_modify_targets:
                res += ["targets"]
        return res

    def has_delete_permission(self, request, obj=None):
        return not (obj and not obj.allow_modify_self)


class TargetAdmin(admin.ModelAdmin):
    def get_list_display(self, request):
        return ("name", "description", "ip_address", "port", "disabled")

    def get_fields(self, request, obj=None):
        return ["name", "description", "ip_address", "port", "disabled", "peer_groups"]

    def get_readonly_fields(self, request, obj=None):
        res = []
        if obj:
            if not obj.allow_modify_self:
                res += [
                    "name",
                    "description",
                    "disabled",
                    "ip_address",
                    "port",
                ]
            if not obj.allow_modify_peer_groups:
                res += ["peer_groups"]
        return res

    def has_delete_permission(self, request, obj=None):
        return not (obj and not obj.allow_modify_self)


class ServerConfigurationAdmin(admin.ModelAdmin):
    def get_list_display(self, request):
        return ("host_name_external", "network_address", "port_external", "port_internal")

    def get_fields(self, request, obj=None):
        return [
            "host_name_external",
            "network_address",
            "port_external",
            "port_internal",
            "peer_default_port",
            "wireguard_config_path",
            "script_path_post_down",
            "script_path_post_up",
        ]

    def get_readonly_fields(self, request, obj=None):
        res = ["wireguard_config_path", "script_path_post_down", "script_path_post_up"]
        return res

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Peer, PeerAdmin)
admin.site.register(PeerGroup, PeerGroupAdmin)
admin.site.register(Target, TargetAdmin)
admin.site.register(ServerConfiguration, ServerConfigurationAdmin)
