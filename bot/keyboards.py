from math import ceil, floor

from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.db.models import QuerySet
from django.conf import settings

from telebot.types import InlineKeyboardMarkup

from bot import handlers
from dictionary.models import Dictionary, Language, Phrase
from dictionary.querysets import PhraseQuerySet


def dict_list(qs: QuerySet) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()

    buttons = [
        handlers.select_dictionary(d.name, d.id)
        for d in qs[:6]   # TODO: pagination
    ]

    keyboard.add(*buttons)
    return keyboard


def dictionary_actions(d: Dictionary, user: User) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()

    for (src, dst) in d.language_combinations():
        keyboard.row(
            handlers.dict_training(
                _('Start training {0}-{1}').format(src.code.upper(), dst.code.upper()),
                dict_id=d.id, src_lang_id=src.id, dst_lang_id=dst.id
            ),
            handlers.dict_contents(
                _('View {0}-{1} contents').format(src.code.upper(), dst.code.upper()),
                dict_id=d.id, src_lang_id=src.id, dst_lang_id=dst.id,
                offset=0, count=settings.DICT_CONTENTS_PAGE_SIZE
            )
        )

    actions = []
    if user.has_perm('delete_dictionary', d):
        actions += [handlers.delete_dictionary_request(_('Delete'), d.id)]

    actions += [handlers.list_dicts_callback(_('Back to list'))]
    keyboard.add(*actions)
    return keyboard


def delete_dictionary_confirm(d: Dictionary) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(
        handlers.dict_delete_confirm(_('Delete'), d.id),
        handlers.select_dictionary(_('Cancel'), d.id),
    )
    return kb


# noinspection PyTypeChecker
def dict_contents_paginator(d: Dictionary, queryset: PhraseQuerySet, offset: int, count: int, src_lang: Language, dst_lang: Language) -> InlineKeyboardMarkup:
    total_count = queryset.count()
    params = dict(count=count, src_lang_id=src_lang.id, dst_lang_id=dst_lang.id)
    page = floor(offset / count) + 1
    last_page = ceil(total_count / count)
    actions = []

    if page > 1:
        actions.append(handlers.dict_contents(_('Page 1'), dict_id=d.id, offset=0, **params))

        if page > 2:
            actions.append(handlers.dict_contents(_('Page %d') % (page - 1), dict_id=d.id, offset=offset - count, **params))

    if page < last_page:
        if page < last_page - 1:
            actions.append(handlers.dict_contents(_('Page %d') % (page + 1), dict_id=d.id, offset=offset + count, **params))

        actions.append(handlers.dict_contents(_('Page %d') % last_page, dict_id=d.id, offset=(last_page - 1) * count, **params))

    actions.append(handlers.select_dictionary(_('Back'), d.id))
    kb = InlineKeyboardMarkup()
    kb.row(*actions)
    return kb


def training(d: Dictionary, phrase: Phrase, dst_lang: Language) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(
        handlers.dict_training_phrase(_('Yes'), dict_id=d.id, phrase_id=phrase.id, dst_lang_id=dst_lang.id, is_guessed=1),
        handlers.dict_training_phrase(_('No'), dict_id=d.id, phrase_id=phrase.id, dst_lang_id=dst_lang.id, is_guessed=0),
        handlers.training_done(_('Done'), d.id)
    )
    return kb


def back_to_dict(d: Dictionary) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(
        handlers.select_dictionary(_('Dictionary details'), d.id),
        handlers.list_dicts_callback(_('Back to list')),
    )
    return kb
