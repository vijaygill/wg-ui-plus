from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.cache import caches
import traceback


class Command(BaseCommand):
    help = 'Clear django cache'

    def handle(self, *args, **options):
        try:
            for k in settings.CACHES.keys():
                caches[k].clear()
            self.stdout.write(f"Cleared cache '{k}'.")
            self.stdout.write(self.style.SUCCESS('django cache cleared.'))
        except Exception as e:
            raise CommandError('Error:' + traceback.format_exception(e))
