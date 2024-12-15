from django.core.management.base import BaseCommand, CommandError
from api_app.wireguardhelper import WireGuardHelper
from api_app.models import ServerConfiguration
import traceback


class Command(BaseCommand):
    help = 'Restart WireGuard VPN'

    def handle(self, *args, **options):
        try:
            wg = WireGuardHelper()
            sc = ServerConfiguration.objects.all()[0]
            res = wg.restart(serverConfiguration=sc)
            self.stdout.write(f'{res["status"]}')
            self.stdout.write(self.style.SUCCESS('WireGuard VPN restarted.'))
        except Exception as e:
            raise CommandError('Error:' + traceback.format_exception(e))
