# Generated by Django 5.0 on 2024-02-01 19:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_wallbox_uptime'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='rfidtoken',
            constraint=models.UniqueConstraint(fields=('tokenID', 'tokenClass'), name='api_rfidtoken_unique'),
        ),
    ]