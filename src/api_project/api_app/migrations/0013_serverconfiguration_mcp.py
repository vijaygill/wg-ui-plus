from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("api_app", "0012_alter_serverconfiguration_last_changed_datetime")]
    operations = [
        migrations.AddField(
            model_name="serverconfiguration",
            name="mcp_enabled",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="serverconfiguration",
            name="mcp_token",
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
    ]
