import traceback

from api_app.models import Peer, PeerGroup, ServerConfiguration, Target
from api_app.wireguardhelper import WireGuardHelper
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Generate WireGuard Configuration files.'

    def handle(self, *args, **options):
        try:
            wg = WireGuardHelper()
            sc = ServerConfiguration.objects.all()[0]
            peer_groups = PeerGroup.objects.all()
            peers = Peer.objects.all()
            targets = Target.objects.all()
            res = wg.generate_configuration_files(
                serverConfiguration=sc, targets=targets, peer_groups=peer_groups, peers=peers
            )
            self.stdout.write(f'{res["status"]}')
            self.stdout.write(self.style.SUCCESS('Generated WireGuard Configuration Files.'))
        except:
            raise CommandError('Error:' + traceback.format_exc())
