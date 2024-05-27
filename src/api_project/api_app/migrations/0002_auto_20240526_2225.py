from django.db import migrations
from ..db_seed import populate_dictionary_data

class Migration(migrations.Migration):

    dependencies = [
        ('api_app', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(populate_dictionary_data)
    ]
