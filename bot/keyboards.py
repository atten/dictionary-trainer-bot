from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.db.models import QuerySet

from telebot.types import InlineKeyboardMarkup

from bot import handlers
from dictionary.models import Dictionary, Language, Phrase


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
