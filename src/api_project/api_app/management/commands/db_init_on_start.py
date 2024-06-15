#!/usr/bin/python
import os
from django.core.management.base import BaseCommand, CommandError
from api_app.models import ServerConfiguration
import traceback


class Command(BaseCommand):
    help = 'Initialises DB tables.'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        self.update_server_config()

    def update_server_config(self):
        try:
            scs = ServerConfiguration.objects.all()
            for sc in scs:
                is_dirty = False
                host_name_external = os.environ.get("WG_HOST_NAME_EXTERNAL", None)
                if host_name_external and sc.host_name_external != host_name_external:
                    sc.host_name_external = host_name_external
                    is_dirty = True
                    self.stdout.write(self.style.SUCCESS('Updated host_name_external'))
                local_networks = os.environ.get("WG_LOCAL_NETWORKS", None)
                if local_networks and sc.local_networks != local_networks:
                    sc.local_networks = local_networks
                    is_dirty = True
                    self.stdout.write(self.style.SUCCESS('Updated local_networks'))
                upstream_dns_ip_address = os.environ.get("WG_UPSTREAM_DNS_SERVER", None)
                if upstream_dns_ip_address and sc.upstream_dns_ip_address != upstream_dns_ip_address:
                    sc.upstream_dns_ip_address = upstream_dns_ip_address
                    is_dirty = True
                    self.stdout.write(self.style.SUCCESS('Updated upstream_dns_ip_address'))
                port_external = os.environ.get("WG_PORT_EXTERNAL", None)
                if port_external and sc.port_external != port_external:
                    sc.port_external = port_external
                    is_dirty = True
                    self.stdout.write(self.style.SUCCESS('Updated port_external'))
                port_internal = os.environ.get("WG_PORT_INTERNAL", None)
                if port_internal and sc.port_internal != port_internal:
                    sc.port_internal = port_internal
                    is_dirty = True
                    self.stdout.write(self.style.SUCCESS('Updated port_internal'))
                if is_dirty:
                    sc.save()
                    self.stdout.write(self.style.SUCCESS('Updated Server Configuration'))
        except:
            raise CommandError('Error:' + traceback.format_exc())
