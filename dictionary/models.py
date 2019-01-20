import itertools

from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.db import models
from django.db.models import CASCADE
from django.db import IntegrityError, transaction

from model_utils import Choices
from model_utils.models import TimeStampedModel

from dictionary.querysets import LanguageQuerySet, DictionaryQuerySet, PhraseGroupQuerySet, PhraseQuerySet, DictionaryUserStatQuerySet, PhraseUserStatQuerySet
from .exceptions import PhraseGroupCreateError


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

    objects = LanguageQuerySet.as_manager()

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

    objects = PhraseQuerySet.as_manager()

    class Meta:
        unique_together = [
            ['lang', 'user', 'text']
        ]
        verbose_name = _('Phrase')
        verbose_name_plural = _('Phrases')
        ordering = ('text',)

    def __str__(self):
        return f'{self.text} [{self.lang.code}]'

    def translations(self, lang: Language):
        return Phrase.objects.filter(phrase_groups__in=self.phrase_groups.all(), lang=lang)

    def verbose_translations(self, lang: Language) -> str:
        """
        возвращает "Фраза - Перевод1, Перевод2" или "Фраза", если переводов нет.
        переводы находятся с данной фразой в одной PhraseGroup
        """
        translations = list(self.translations(lang).values_list('text', flat=True))
        if not translations:
            return self.text

        translations = ', '.join(translations)
        return f'{self.text} - {translations}'

    def guessed_or_not(self, user, dictionary, is_guessed):
        # добавляет синонимы фразы на том же языке в кэш
        bucket = Phrase.objects.get_user_lang_bucket(user, self.lang)
        self.translations(self.lang).push_recent_phrase(bucket)

        DictionaryUserStat.objects.get_training_stat_for_user(dictionary, user).increment_trained(is_guessed=is_guessed)
        DictionaryUserStat.objects.get_total_stat_for_user(dictionary, user).increment_trained(is_guessed=is_guessed)
        PhraseUserStat.objects.get_stat_for_user(self, user).increment_trained(is_guessed=is_guessed)


class PhraseGroup(TimeStampedModel):
    phrases = models.ManyToManyField(
        Phrase, related_name='phrase_groups',
        help_text=_('Ids of neighbour phrases (synonyms, translations)'))
    user = models.ForeignKey(User, on_delete=CASCADE, related_name='phrase_groups', db_index=True, help_text=_('Author'))
    dictionaries = models.ManyToManyField('Dictionary', related_name='phrase_groups')

    objects = PhraseGroupQuerySet.as_manager()

    class Meta:
        verbose_name = _('Phrase group')
        verbose_name_plural = _('Phrase groups')
        ordering = ('user',)

    def __str__(self):
        return f'PhraseGroup #{self.id}'

    def phrase_for_lang(self, language: Language):
        return self.phrases.filter(lang=language).pick_random()

    @classmethod
    def create_from_input(cls, input_str: str, user: User) -> 'PhraseGroup':
        parts = input_str.split(' - ')
        langs = []
        phrases = []

        for part in parts:
            if not part:
                raise PhraseGroupCreateError(_('Error: Definition contains empty part'))

            lang = Language.objects.detect(part)

            if not lang:
                raise PhraseGroupCreateError(_('Error: Failed to detected phrase language: {}.').format(part))
            if lang in langs:
                raise PhraseGroupCreateError(_('Error: {} language detected twice. '
                                               'Another phrase must me in different language').format(lang))

            phrases_str = [s.strip() for s in part.split(',') if s.strip()]
            if not phrases_str:
                raise PhraseGroupCreateError(_('Error: Empty phrase for language {}').format(lang))

            langs.append(lang)
            phrases += [Phrase(user=user, text=text, lang=lang) for text in phrases_str]

        if len(langs) != 2:
            raise PhraseGroupCreateError(_('Error: Invalid phrases count, expect 2'))

        try:
            with transaction.atomic():
                Phrase.objects.bulk_create(phrases)
                group = PhraseGroup.objects.create(user=user)
                group.phrases.add(*phrases)

            return group
        except IntegrityError:
            # TODO: варианты разруливания
            raise PhraseGroupCreateError('Database error occurs, failed to save phrases to dictionary')


class Dictionary(TimeStampedModel):
    name = models.CharField(max_length=64)
    user = models.ForeignKey(User, on_delete=CASCADE, related_name='dictionaries', help_text=_('Author'))

    editors = models.ManyToManyField(User, related_name='editable_dictionaries', blank=True)    # юзеры с правами на запись
    viewers = models.ManyToManyField(User, related_name='readable_dictionaries', blank=True)    # юзеры с правами на чтение

    objects = DictionaryQuerySet.as_manager()

    class Meta:
        unique_together = [
            ['name', 'user']
        ]
        verbose_name = _('Dictionary')
        verbose_name_plural = _('Dictionaries')
        ordering = ('name', 'user',)

    def __str__(self):
        return self.name

    def languages(self):
        return Language.objects.filter(phrases__phrase_groups__dictionaries=self).distinct()

    def language_combinations(self):
        return itertools.permutations(self.languages(), 2)

    @property
    def phrases(self):
        return Phrase.objects.filter(phrase_groups__dictionaries=self)

    def get_user_training_stats(self, user: User) -> 'DictionaryUserStat':
        return DictionaryUserStat.objects.get_training_stat_for_user(self, user)


class PhraseUserStat(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=CASCADE, related_name='phrase_group_stats')
    phrase = models.ForeignKey(Phrase, on_delete=CASCADE, related_name='user_stats')
    trained_count = models.IntegerField(default=0)
    guessed_count = models.IntegerField(default=0)
    guessed_ratio = models.FloatField(default=0)

    objects = PhraseUserStatQuerySet.as_manager()

    class Meta:
        unique_together = [
            ['user', 'phrase']
        ]
        verbose_name = _('Phrase user stat')
        verbose_name_plural = _('Phrase user stats')

    def __str__(self):
        return _('Phrase user stat #{0}').format(self.id)

    def increment_trained(self, is_guessed: bool=False):
        self.trained_count += 1
        if is_guessed:
            self.guessed_count += 1

        self.guessed_ratio = 1.0 * self.guessed_count / self.trained_count
        self.save()


class DictionaryUserStat(TimeStampedModel):
    KIND = Choices('training', 'total')

    user = models.ForeignKey(User, on_delete=CASCADE, related_name='dictionary_stats')
    dict = models.ForeignKey(Dictionary, on_delete=CASCADE, related_name='user_stats')
    kind = models.CharField(max_length=32, choices=KIND)
    trained_count = models.IntegerField(default=0)
    guessed_count = models.IntegerField(default=0)

    objects = DictionaryUserStatQuerySet.as_manager()

    class Meta:
        unique_together = [
            ['user', 'dict', 'kind']
        ]
        verbose_name = _('Dictionary user stat')
        verbose_name_plural = _('Dictionary user stats')

    def __str__(self):
        return _('Dictionary user stat #{0}').format(self.id)

    @property
    def guessed_ratio(self) -> float:
        return 1.0 * self.guessed_count / self.trained_count if self.trained_count else 0.0

    def increment_trained(self, is_guessed: bool=False):
        self.trained_count += 1
        if is_guessed:
            self.guessed_count += 1
        self.save()

    def is_training_completed(self, src_lang: Language, dst_lang: Language):
        # если кол-во тренированных слов совпадает с числом групп фраз, содержащих слова на обоих языках
        groups_count = self.dict.phrase_groups.filter(phrases__lang=src_lang).filter(phrases__lang=dst_lang).count()
        return self.trained_count >= groups_count

    def get_progress(self, language=None):
        phrases_qs = self.dict.phrases
        if language:
            phrases_qs = phrases_qs.filter(lang=language)

        trained_phrases_qs = phrases_qs.filter(user_stats__user=self.user, user_stats__trained_count__gt=0)

        phrases_count = phrases_qs.count()
        trained_phrases_count = trained_phrases_qs.count()
        trained_ratio = 1.0 * trained_phrases_count / phrases_count if phrases_count else 0

        return {
            'phrases_count': phrases_count,
            'trained_phrases_count': trained_phrases_count,
            'trained_ratio': trained_ratio
        }
