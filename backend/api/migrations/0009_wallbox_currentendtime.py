# Generated by Django 5.0.3 on 2024-04-06 16:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_wallbox_currentenergymeteratstart_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='wallbox',
            name='currentEndTime',
            field=models.DateTimeField(default=None, null=True),
        ),
    ]