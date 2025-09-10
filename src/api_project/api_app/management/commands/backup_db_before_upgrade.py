import os
import shutil
import traceback
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from api_app.common import RUNTIME_ENV_LIVE


class Command(BaseCommand):
    help = "Backup database before upgrade"

    def handle(self, *args, **options):
        try:
            db_file_path = settings.DATABASES['default']['NAME']
            db_file_dir = os.path.dirname(db_file_path)
            db_file_name = os.path.basename(db_file_path)
            image_stage = os.environ.get("IMAGE_STAGE", None)
            new_version = os.environ.get("APP_VERSION", None)
            if new_version and (not new_version.startswith("v")):
                new_version = None
            if RUNTIME_ENV_LIVE != image_stage:
                image_stage = None
            if image_stage and new_version:
                backup_file = f"{db_file_dir}/{db_file_name}-before-{new_version}"
                if os.path.exists(backup_file):
                    self.stdout.write(self.style.SUCCESS(f"Database backup exists already: {backup_file}."))
                else:
                    self.stdout.write("Database needs backup.")
                    shutil.copyfile(db_file_path, backup_file)
                    self.stdout.write(
                        self.style.SUCCESS(f"Database backed up to {backup_file}.")
                    )
        except Exception as e:
            raise CommandError("Error:" + traceback.format_exception(e))
