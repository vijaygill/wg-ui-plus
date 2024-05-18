from django.contrib import admin

from .models import Peer, PeerGroup, Target

class PeerAdmin(admin.ModelAdmin):
  list_display = ("name", "description", "ip_address", "disabled")

class PeerGroupAdmin(admin.ModelAdmin):
  list_display = ("name", "description", "disabled")

  def get_fields(self, request, obj=None):
    return ['name', 'description', 'peers', 'targets']

  def get_readonly_fields(self, request, obj=None):
    if obj and not obj.allow_modify_self:
        return ['name', 'description']
    return []

class TargetAdmin(admin.ModelAdmin):
  list_display = ("name", "description", "ip_address", "port", "disabled")

admin.site.register(Peer, PeerAdmin)
admin.site.register(PeerGroup, PeerGroupAdmin)
admin.site.register(Target, TargetAdmin)
