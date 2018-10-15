from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.db import models
from django.db.models import QuerySet, CASCADE

from model_utils.models import TimeStampedModel


class Language(models.Model):
    name = models.CharField(
        _('Name'), unique=True, max_length=50,
        help_text='The name of the language including dialect, script, etc.')
    code = models.CharField(
        _('Code'), unique=True, max_length=50,
        help_text=_('The primary language code, used in file naming, etc. (e.g. pt_BR for Brazilian Portuguese.)'))
    code_aliases = models.CharField(
        _('Code aliases'), max_length=100,
        help_text=_('A space-separated list of alternative locales.'), null=True, blank=True, default='')
    priority = models.IntegerField(_('Priority'), default=0)

    class Meta:
        index_together = [
            ['code'], ['code', 'code_aliases']
        ]
        verbose_name = _('Language')
        verbose_name_plural = _('Languages')
        ordering = ('-priority', 'name')

    def __str__(self):
        return '%s [%s]' % (_(self.name), self.code)

    @property
    def localized_name(self) -> str:
        """Название языка в текущей локали."""
        return _(self.name)


class Phrase(TimeStampedModel):
    lang = models.ForeignKey(Language, on_delete=CASCADE, related_name='phrases')
    user = models.ForeignKey(User, on_delete=CASCADE, related_name='phrases', help_text=_('Author'))
    text = models.CharField(max_length=255)

    class Meta:
        unique_together = [
            ['lang', 'user', 'text']
        ]
        verbose_name = _('Phrase')
        verbose_name_plural = _('Phrases')
        ordering = ('text',)

    def __str__(self):
        return f'{self.text} [{self.lang.code}]'


class PhraseAlias(TimeStampedModel):
    phrases = models.ManyToManyField(
        Phrase, related_name='phrase_aliases',
        help_text=_('Ids of neighbour phrases (synonyms, translations)'))
    user = models.ForeignKey(User, on_delete=CASCADE, related_name='phrase_aliases', db_index=True, help_text=_('Author'))

    class Meta:
        verbose_name = _('Phrase Alias')
        verbose_name_plural = _('Phrase Aliases')
        ordering = ('user',)

    def __str__(self):
        return f'PhraseAlias #{self.id}'


class Dictionary(TimeStampedModel):
    name = models.CharField(max_length=64)
    user = models.ForeignKey(User, on_delete=CASCADE, related_name='dictionaries', help_text=_('Author'))
    phrase_aliases = models.ManyToManyField(PhraseAlias, related_name='dictionaries')

    class Meta:
        unique_together = [
            ['name', 'user']
        ]
        verbose_name = _('Dictionary')
        verbose_name_plural = _('Dictionaries')
        ordering = ('name', 'user',)
