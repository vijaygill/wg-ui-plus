# Generated by Django 5.0.6 on 2024-05-18 20:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0002_alter_peergroup_targets_alter_target_peer_groups'),
    ]

    operations = [
        migrations.AlterField(
            model_name='peer',
            name='ip_address',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
