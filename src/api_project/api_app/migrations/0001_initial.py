# Generated by Django 5.0.6 on 2024-05-21 17:07

import api_app.models
from django.db import migrations, models
from ..db_seed import populate_dictionary_data




class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Peer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.CharField(max_length=255, null=True)),
                ('disabled', models.BooleanField(default=False, null=True)),
                ('ip_address', models.CharField(blank=True, max_length=255, null=True)),
                ('port', models.IntegerField(blank=True, null=True)),
                ('public_key', models.CharField(blank=True, max_length=255, null=True)),
                ('private_key', models.CharField(blank=True, max_length=255, null=True)),
                ('last_changed_datetime', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='ServerConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('network_address', models.CharField(max_length=255, validators=[api_app.models.is_network_address])),
                ('host_name_external', models.CharField(max_length=255)),
                ('port_external', models.IntegerField()),
                ('port_internal', models.IntegerField()),
                ('upstream_dns_ip_address', models.CharField(max_length=255)),
                ('wireguard_config_path', models.CharField(max_length=255)),
                ('script_path_post_down', models.CharField(max_length=255)),
                ('script_path_post_up', models.CharField(max_length=255)),
                ('public_key', models.CharField(blank=True, max_length=255, null=True)),
                ('private_key', models.CharField(blank=True, max_length=255, null=True)),
                ('peer_default_port', models.IntegerField()),
                ('last_changed_datetime', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='PeerGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.CharField(max_length=255, null=True)),
                ('disabled', models.BooleanField(default=False, null=True)),
                ('allow_modify_self', models.BooleanField(default=True, null=True)),
                ('allow_modify_peers', models.BooleanField(default=True, null=True)),
                ('allow_modify_targets', models.BooleanField(default=True, null=True)),
                ('last_changed_datetime', models.DateTimeField(auto_now=True)),
                ('peers', models.ManyToManyField(blank=True, to='api_app.peer')),
            ],
        ),
        migrations.AddField(
            model_name='peer',
            name='peer_groups',
            field=models.ManyToManyField(blank=True, to='api_app.peergroup'),
        ),
        migrations.CreateModel(
            name='Target',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.CharField(blank=True, max_length=255, null=True)),
                ('disabled', models.BooleanField(default=False, null=True)),
                ('ip_address', models.CharField(max_length=255, validators=[api_app.models.is_network_or_single_address])),
                ('port', models.IntegerField(blank=True, null=True)),
                ('allow_modify_self', models.BooleanField(default=True, null=True)),
                ('allow_modify_peer_groups', models.BooleanField(default=True, null=True)),
                ('last_changed_datetime', models.DateTimeField(auto_now=True)),
                ('peer_groups', models.ManyToManyField(blank=True, to='api_app.peergroup')),
            ],
        ),
        migrations.AddField(
            model_name='peergroup',
            name='targets',
            field=models.ManyToManyField(blank=True, to='api_app.target'),
        ),
        migrations.RunPython(populate_dictionary_data),
    ]