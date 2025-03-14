from django.core.management.base import BaseCommand, CommandError
from django.core.cache import cache
import traceback


class Command(BaseCommand):
    help = 'Clear django cache'

    def handle(self, *args, **options):
        try:
            cache.clear()
            self.stdout.write(self.style.SUCCESS('django cache cleared.'))
        except Exception as e:
            raise CommandError('Error:' + traceback.format_exception(e))
