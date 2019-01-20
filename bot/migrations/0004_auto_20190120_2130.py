# Generated by Django 2.1.2 on 2019-01-20 18:30

import bot.models
from django.db import migrations, models
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0003_telegramlogentry_text_length'),
    ]

    operations = [
        migrations.AddField(
            model_name='telegramprofile',
            name='created',
            field=model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created'),
        ),
        migrations.AddField(
            model_name='telegramprofile',
            name='modified',
            field=model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified'),
        ),
        migrations.AlterField(
            model_name='telegramlogentry',
            name='version',
            field=models.CharField(default=bot.models.current_version, editable=False, max_length=64),
        ),
    ]
