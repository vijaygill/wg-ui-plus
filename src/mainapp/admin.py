from django.contrib import admin

from .models import Peer, PeerGroup, Target

class PeerAdmin(admin.ModelAdmin):
  list_display = ("name", "description", "ip_address", "disabled")

class PeerGroupAdmin(admin.ModelAdmin):
  list_display = ("name", "description", "disabled", )

  def get_fields(self, request, obj=None):
    return ['name', 'description', 'disabled', 'peers', 'targets']

  def get_readonly_fields(self, request, obj=None):
    res = []
    if obj:
      if not obj.allow_modify_self:
          res += ['name', 'description', 'disabled']
      if not obj.allow_modify_peers:
          res += ['peers']
      if not obj.allow_modify_targets:
          res += ['targets']
    return res

class TargetAdmin(admin.ModelAdmin):
  list_display = ("name", "description", "ip_address", "port", "disabled")
  
  def get_fields(self, request, obj=None):
    return ['name', 'description',"ip_address", "port", 'disabled', 'peer_groups']

  def get_readonly_fields(self, request, obj=None):
    res = []
    if obj:
      if not obj.allow_modify_self:
          res += ['name', 'description', 'disabled',"ip_address", "port",]
      if not obj.allow_modify_peer_groups:
          res += ['peer_groups']
    return res

admin.site.register(Peer, PeerAdmin)
admin.site.register(PeerGroup, PeerGroupAdmin)
admin.site.register(Target, TargetAdmin)
