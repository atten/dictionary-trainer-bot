import random
from typing import List
from string import ascii_letters

from django.core.cache import cache
from django.db.models import QuerySet, Q
from django.contrib.auth.models import User
from django.conf import settings


class LanguageQuerySet(QuerySet):

    def detect(self, text: str):
        if not text:
            return

        # TODO: годится только для internal use
        if text[0] in ascii_letters:
            return self.get(code='en')
        return self.get(code='ru')


class RandomizeQuerySet(QuerySet):

    def pick_random(self):
        ids = self.values_list('id', flat=True)
        return self.get(id=random.choice(ids)) if ids else None


class DictionaryQuerySet(QuerySet):

    def for_user(self, user: User):
        return self.filter(Q(user=user) | Q(viewers=user) | Q(editors=user)).distinct()


class PhraseQuerySet(RandomizeQuerySet):

    @staticmethod
    def get_user_lang_bucket(user: User, lang) -> str:
        return f'user:{user.id}:lang:{lang.id}:recent_phrases'

    @staticmethod
    def get_recent_phrases_ids(bucket: str) -> List[str]:
        d = cache.get(bucket)
        return d.split(',') if d else []

    def get_recent_phrases(self, bucket: str):
        return self.filter(id__in=self.get_recent_phrases_ids(bucket))

    def push_recent_phrase(self, bucket: str):
        """
        добавляет в кэшированный список последних фраз юзера новый id в начало,
        при этом обрезая список с конца при необходимости
        """
        ids = self.get_recent_phrases_ids(bucket)
        new_ids = list(map(lambda x: str(x), self.values_list('id', flat=True)))
        for i in new_ids:
            if i in ids:
                ids.remove(i)

        ids = new_ids + ids
        d = ','.join(ids[0:settings.RECENT_PHRASES])
        cache.set(bucket, d)

    def get_next_for_training(self, user: User, dictionary, src_lang, dst_lang):
        """первое нетренированное слово из словаря, либо наименее тренированное"""
        qs = self.filter(phrase_groups__dictionaries=dictionary, lang=src_lang)\
            .filter(phrase_groups__phrases__lang=dst_lang).distinct()

        recent_ids = self.get_recent_phrases_ids(self.get_user_lang_bucket(user, src_lang))

        # первое нетренированное слово из словаря
        phrase = qs.exclude(user_stats__user=user, id__in=recent_ids).pick_random()
        if not phrase:
            # тренированные слова, начиная с наимеее угаданного
            qs = qs.filter(user_stats__user=user).order_by('user_stats__guessed_ratio')

            # возвращаем первое слово не из буффера
            # если таких нет, то последнее из буффера
            if qs.count() > len(recent_ids):
                return qs.exclude(id__in=recent_ids).first()
            return self.get(id=recent_ids[-1])
        return phrase


class PhraseGroupQuerySet(RandomizeQuerySet):
    pass


class PhraseUserStatQuerySet(QuerySet):

    def get_stat_for_user(self, phrase, user: User):
        obj, created = self.get_or_create(user=user, phrase=phrase)
        return obj


class DictionaryUserStatQuerySet(QuerySet):

    def get_total_stat_for_user(self, dictionary, user: User):
        obj, created = self.get_or_create(user=user, dict=dictionary, kind='total')
        return obj

    def get_training_stat_for_user(self, dictionary, user: User):
        obj, created = self.get_or_create(user=user, dict=dictionary, kind='training')
        return obj
