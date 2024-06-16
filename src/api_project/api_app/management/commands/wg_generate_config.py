from django.core.management.base import BaseCommand, CommandError
from api_app.wireguardhelper import WireGuardHelper
from api_app.models import ServerConfiguration, PeerGroup, Peer, Target
import traceback


class Command(BaseCommand):
    help = 'Generate WireGuard Configuration files.'

    def handle(self, *args, **options):
        try:
            wg = WireGuardHelper()
            sc = ServerConfiguration.objects.all()[0]
            peer_groups = PeerGroup.objects.all()
            peers = Peer.objects.all()
            targets = Target.objects.all()
            res = wg.generateConfigurationFiles(
                serverConfiguration=sc, targets=targets, peer_groups=peer_groups, peers=peers
            )
            self.stdout.write(f'{res["status"]}')
            self.stdout.write(self.style.SUCCESS('Generated WireGuard Configuration Files.'))
        except:
            raise CommandError('Error:' + traceback.format_exc())
