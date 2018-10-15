# Generated by Django 2.1.2 on 2018-10-15 08:06

from django.conf import settings
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dictionary', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Dictionary',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('name', models.CharField(max_length=64)),
            ],
            options={
                'verbose_name': 'Dictionary',
                'verbose_name_plural': 'Dictionaries',
                'ordering': ('name', 'user'),
            },
        ),
        migrations.CreateModel(
            name='Phrase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('text', models.CharField(max_length=255)),
                ('lang', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='phrases', to='dictionary.Language')),
                ('user', models.ForeignKey(help_text='Author', on_delete=django.db.models.deletion.CASCADE, related_name='phrases', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Phrase',
                'verbose_name_plural': 'Phrases',
                'ordering': ('text',),
            },
        ),
        migrations.CreateModel(
            name='PhraseAlias',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('phrases', django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(), help_text='Ids of neighbour phrases (synonyms, translations)', size=32)),
                ('user', models.ForeignKey(help_text='Author', on_delete=django.db.models.deletion.CASCADE, related_name='phrase_aliases', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Phrase Alias',
                'verbose_name_plural': 'Phrase Aliases',
                'ordering': ('user',),
            },
        ),
        migrations.AddField(
            model_name='dictionary',
            name='phrase_aliases',
            field=models.ManyToManyField(related_name='dictionaries', to='dictionary.PhraseAlias'),
        ),
        migrations.AddField(
            model_name='dictionary',
            name='user',
            field=models.ForeignKey(help_text='Author', on_delete=django.db.models.deletion.CASCADE, related_name='dictionaries', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='phrase',
            unique_together={('lang', 'user', 'text')},
        ),
        migrations.AlterUniqueTogether(
            name='dictionary',
            unique_together={('name', 'user')},
        ),
    ]
