from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver


# Create your models here.
class PeerGroup(models.Model):
  name = models.CharField(max_length = 255)
  description = models.CharField(max_length = 255, null = True)
  disabled = models.BooleanField(null = True, default = False)
  allow_modify_self = models.BooleanField(null = True, default = True)
  allow_modify_peers = models.BooleanField(null = True, default = True)
  allow_modify_targets = models.BooleanField(null = True, default = True)
  peers = models.ManyToManyField('Peer', blank=True)
  targets = models.ManyToManyField('Target', blank=True)

  def __str__(self):
     return f"{self.name} - {self.description}"

class Peer(models.Model):
  name = models.CharField(max_length = 255)
  description = models.CharField(max_length = 255, null = True)
  disabled = models.BooleanField(null = True, default = False)
  ip_address = models.CharField(max_length = 255, null = True, blank=True)
  port = models.IntegerField(null = True, blank=True)
  public_key = models.CharField(max_length = 255, null = True, blank=True)
  private_key = models.CharField(max_length = 255, null = True, blank=True)
  peer_groups = models.ManyToManyField('PeerGroup', blank=True, through=PeerGroup.peers.through, )

  def __str__(self):
     return f"{self.name} - {self.description}"
  
  def save(self, force_insert=False, force_update=False, **kwargs):
    pg = PeerGroup.objects.filter(name = 'Everyone')
    if pg:
      self.peer_group.add(pg[0])
    super(Peer, self).save(force_insert, force_update)

class Target(models.Model):
  name = models.CharField(max_length = 255)
  description = models.CharField(max_length = 255, null = True, blank=True)
  disabled = models.BooleanField(null = True, default = False)
  ip_address = models.CharField(max_length = 255, null = True, blank=True)
  port = models.IntegerField(null = True, blank=True)
  allow_modify_self = models.BooleanField(null = True, default = True)
  allow_modify_peer_groups = models.BooleanField(null = True, default = True)
  peer_groups = models.ManyToManyField('PeerGroup', blank=True, through=PeerGroup.targets.through, )

  def __str__(self):
     return f"{self.name} - {self.description}"

class ServerConfiguration(models.Model):
  ip_address= models.CharField(max_length = 255)
  host_name_external= models.CharField(max_length = 255)
  port_external= models.IntegerField()
  port_internal= models.IntegerField()
  wireguard_config_path= models.CharField(max_length = 255)
  script_path_post_down= models.CharField(max_length = 255)
  script_path_post_up= models.CharField(max_length = 255)
  public_key= models.CharField(max_length = 255, null = True, blank = True)
  private_key= models.CharField(max_length = 255, null = True, blank = True)
  peer_default_port = models.IntegerField()

  def __str__(self):
     return f"{self.host_name_external} - {self.port_external}"

