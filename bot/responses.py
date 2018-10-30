from django.contrib.auth.models import User
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _, ngettext, gettext
from django.db import IntegrityError, transaction
from django.db.models import QuerySet

from telebot.types import Message, CallbackQuery

from bot.models import TelegramLogEntry, TelegramMessageEntity
from bot import keyboards as kb
from bot.commands import COMMANDS, commands_as_text
from bot import bot
from dictionary.exceptions import PhraseGroupCreateError
from dictionary.models import Dictionary, Language, Phrase, DictionaryUserStat, PhraseGroup


class Response:
    def __init__(self, text, reply_markup=None, parse_mode=None):
        self.text = text
        self.reply_markup = reply_markup
        self.parse_mode = parse_mode

    def __str__(self):
        return force_text(self.text)

    def answer_to(self, msg: Message):
        bot.send_message(
            msg.chat.id,
            force_text(self.text),
            reply_markup=self.reply_markup,
            parse_mode=self.parse_mode
        )

        TelegramLogEntry.objects.create(
            text=msg.text[:128],
            profile_id=msg.chat.id,
            response=str(self)[:128]
        )

    def answer_to_callback(self, callback: CallbackQuery):
        bot.send_message(
            callback.message.chat.id,
            force_text(self.text),
            reply_markup=self.reply_markup,
            parse_mode=self.parse_mode
        )

        TelegramLogEntry.objects.create(
            text=callback.data[:128],
            profile_id=callback.message.chat.id,
            response=str(self)[:128]
        )

    def replace_prev(self, callback: CallbackQuery):
        msg = callback.message
        bot.edit_message_text(
            force_text(self.text),
            chat_id=msg.chat.id,
            message_id=msg.message_id,
            reply_markup=self.reply_markup,
            parse_mode=self.parse_mode
        )

        TelegramLogEntry.objects.create(
            text=callback.data[:128],
            profile_id=msg.chat.id,
            response=str(self)[:128]
        )


def commands_list(text=None) -> Response:
    return Response(
        commands_as_text() if not text else text + '\n' + commands_as_text()
    )


def select_your_dictionary(qs: QuerySet, text=None) -> Response:
    text_default = _('Select active dictionary:')
    return Response(
        text=f'{text}\n{text_default}' if text else text_default,
        reply_markup=kb.dict_list(qs)
    )


def your_dict_list_is_empty() -> Response:
    return Response(
        text=_('You have no dictionaries. Create new: %s') % COMMANDS.create_dict,
    )


def dict_list(qs: QuerySet, text=None) -> Response:
    return select_your_dictionary(qs, text) if qs.count() else your_dict_list_is_empty()


def current_dictionary_detail(user: User) -> Response:
    dictionary = user.tg.current_dict
    return dictionary_detail(dictionary, user) if dictionary else your_dict_list_is_empty()


def dictionary_detail(dictionary: Dictionary, user: User) -> Response:
    user.tg.current_dict = dictionary
    user.tg.save()

    stat = DictionaryUserStat.objects.get_total_stat_for_user(dictionary, user)
    stat_dict = {
        'all': stat.get_progress()
    }

    for l in dictionary.languages():
        stat_dict[l.localized_name] = stat.get_progress(l)

    lines = [
        _('Dictionary: <b>%s</b>') % dictionary.name,
        _('{0} entries').format(dictionary.phrase_groups.count()),
        _('Training progress:')
    ]

    for k, v in stat_dict.items():
        lines.append(_(' - {0}: {1}/{2} words ({3:.2%})').format(k, v['trained_phrases_count'], v['phrases_count'], v['trained_ratio']))

    lines.append(_('What do you want to do?'))
    lines = [force_text(s) for s in lines]
    return Response(
        text='\n'.join(lines),
        parse_mode='HTML',
        reply_markup=kb.dictionary_actions(dictionary, user)
    )


def dictionary_create_error(name: str) -> Response:
    return Response(
        text=_('Dictionary "%s" already exists, try another name:') % name
    )


def create_dictionary_input() -> Response:
    return Response(
        text=_('Input a name for your new dictionary, e.g. "Primary dict" (or "Phrasebook" or "Test" etc):')
    )


def create_dictionary(user: User, name: str) -> Response:
    try:
        dictionary = Dictionary.objects.create(
            user=user,
            name=name
        )
        user.tg.current_dict = dictionary
        user.tg.reset_state()
        return dictionary_detail(dictionary, user)
    except IntegrityError:
        return dictionary_create_error(name)


def delete_dictionary_request(dictionary: Dictionary) -> Response:
    return Response(
        text=_('Confirm deleting of dictionary <b>{0}</b>:').format(dictionary),
        parse_mode='HTML',
        reply_markup=kb.delete_dictionary_confirm(dictionary)
    )


def training(user: User, dictionary: Dictionary, src_lang: Language, dst_lang: Language) -> Response:
    phrase = Phrase.objects.get_next_for_training(user, dictionary, src_lang, dst_lang)
    if not phrase:
        qs = Dictionary.objects.for_user(user)
        return dict_list(qs, _('No available phrases found.'))

    return Response(
        text=phrase.text,
        reply_markup=kb.training(dictionary, phrase, dst_lang)
    )


def training_done(stats: DictionaryUserStat) -> Response:
    lines = [
        _('Training results:'),
        _('  trained words count: {}').format(stats.trained_count),
        _('  guessed: {0:.2%}').format(stats.guessed_ratio)
    ]
    lines = [force_text(s) for s in lines]
    return Response(
        text='\n'.join(lines),
        reply_markup=kb.back_to_dict(stats.dict)
    )


def add_phrase_groups(user: User, msg: Message) -> Response:
    dictionary = user.tg.current_dict

    if not dictionary:
        return commands_list(_('You should select or create dictionary first.'))

    if not user.has_perm('add_phrasegroup', dictionary):
        return Response(_('Error: you are not allowed to add phrases to dictionary "{}"').format(dictionary))

    groups_count = 0
    phrases_count = 0
    try:
        with transaction.atomic():
            for line in msg.text.split('\n'):
                group = PhraseGroup.create_from_input(line, user)
                dictionary.phrase_groups.add(group)
                groups_count += 1
                phrases_count += group.phrases.count()

                msg_entity = TelegramMessageEntity.objects.create(chat_id=msg.chat.id, message_id=msg.message_id)
                msg_entity.phrases.add(*list(group.phrases.ids()))
    except PhraseGroupCreateError as e:
        return Response(e)

    phrases_verbose = ngettext(_('phrase'), _('phrases'), phrases_count)
    groups_verbose = ngettext(_('group'), _('groups'), groups_count)

    return Response(
        text=_('Added {} {} with {} {} to dictionary "{}"').format(groups_count, groups_verbose, phrases_count,
                                                                   phrases_verbose, dictionary)
    )


def replace_phrase_groups(user, msg: Message) -> Response:
    entity = TelegramMessageEntity.objects.filter(chat_id=msg.chat.id, message_id=msg.message_id).first()

    if not entity or not entity.phrases.count():
        return Response('Nothing to edit (no phrases found in this message)')

    entity.phrases.delete()
    entity.delete()
    resp = add_phrase_groups(user, msg)
    resp.text = resp.text.replace(gettext('Added'), gettext('Edited'))
    return resp
