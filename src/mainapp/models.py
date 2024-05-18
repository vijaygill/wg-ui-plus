from django.db import models

# Create your models here.
class PeerGroup(models.Model):
  name = models.CharField(max_length = 255)
  description = models.CharField(max_length = 255, null = True)
  disabled = models.BooleanField(null = True)
  allow_modify_self = models.BooleanField(null = True)
  allow_modify_peers = models.BooleanField(null = True)
  allow_modify_targets = models.BooleanField(null = True)
  targets = models.ManyToManyField('Target', blank=True)

  def __str__(self):
     return f"{self.name} - {self.description}"

class Peer(models.Model):
  name = models.CharField(max_length = 255)
  description = models.CharField(max_length = 255, null = True)
  disabled = models.BooleanField(null = True)
  ip_address = models.CharField(max_length = 255, null = True)
  port = models.IntegerField(null = True)
  public_key = models.CharField(max_length = 255, null = True)
  private_key = models.CharField(max_length = 255, null = True)
  peer_group = models.ForeignKey(PeerGroup, on_delete=models.CASCADE, null = True)

  def __str__(self):
     return f"{self.name} - {self.description}"

class Target(models.Model):
  name = models.CharField(max_length = 255)
  description = models.CharField(max_length = 255, null = True)
  disabled = models.BooleanField(null = True)
  ip_address = models.CharField(max_length = 255, null = True)
  port = models.IntegerField(null = True)
  allow_modify_self = models.BooleanField(null = True)
  allow_modify_peergroups = models.BooleanField(null = True)
  peer_groups = models.ManyToManyField('PeerGroup', blank=True)

  def __str__(self):
     return f"{self.name} - {self.description}"
