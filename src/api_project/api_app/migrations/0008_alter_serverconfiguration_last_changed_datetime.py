# Generated by Django 5.1.4 on 2024-12-13 17:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_app', '0007_serverconfiguration_strict_allowed_ips_in_peer_config'),
    ]

    operations = [
        migrations.AlterField(
            model_name='serverconfiguration',
            name='last_changed_datetime',
            field=models.DateTimeField(),
        ),
    ]
