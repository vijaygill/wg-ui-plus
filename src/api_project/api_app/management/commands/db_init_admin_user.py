#!/usr/bin/python
import traceback

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

DEFAULT_ADMIN_USER_NAME = 'admin'
DEFAULT_ADMIN_USER_PASSWORD = 'admin'


class Command(BaseCommand):
    help = 'Creates admin user if not present already. This is not Django super user.'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        try:
            user = User.objects.filter(username=DEFAULT_ADMIN_USER_NAME)
            if user:
                user = user[0]
            if not user:
                user = User.objects.create_user(DEFAULT_ADMIN_USER_NAME, "", DEFAULT_ADMIN_USER_PASSWORD)
                user.save()
                self.stdout.write(self.style.SUCCESS('Admin user initialised successfully.'))
            else:
                self.stdout.write(self.style.SUCCESS('Admin user exists already.'))
        except:
            raise CommandError('Error:' + traceback.format_exc())
