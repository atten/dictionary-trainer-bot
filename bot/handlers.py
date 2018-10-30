from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from telebot.types import Message, CallbackQuery

from bot import responses
from bot.models import USER_STATES
from bot.utils import get_user, CallbackHandler, str_to_int
from bot import bot
from dictionary.models import Dictionary, Language, Phrase, DictionaryUserStat


@bot.message_handler(commands=['start'])
def start(msg: Message):
    user = get_user(msg)
    responses.commands_list(_("Hi %s!") % user.first_name).answer_to(msg)


@bot.message_handler(commands=['create_dict'])
def create_dict(msg: Message):
    get_user(msg)
    responses.create_dictionary_input().answer_to(msg)


@bot.message_handler(commands=['dict_detail'])
def dict_detail(msg: Message):
    user = get_user(msg)
    responses.current_dictionary_detail(user).answer_to(msg)


@bot.message_handler(commands=['list_dicts'])
def list_dicts(msg: Message):
    user = get_user(msg)
    qs = Dictionary.objects.for_user(user)
    responses.dict_list(qs).answer_to(msg)


@CallbackHandler
def list_dicts_callback(callback: CallbackQuery, user: User):
    qs = Dictionary.objects.for_user(user)
    responses.dict_list(qs).replace_prev(callback)


@CallbackHandler
def select_dictionary(callback: CallbackQuery, user: User, dict_id: str):
    qs = Dictionary.objects.for_user(user)
    dictionary = qs.filter(id=dict_id).first()
    if dictionary:
        responses.dictionary_detail(dictionary, user).replace_prev(callback)
    else:
        responses.dict_list(qs, text=_('Dictionary not found.')).replace_prev(callback)


@CallbackHandler
def dict_contents(callback: CallbackQuery, user: User, dict_id: str, offset: str, count: str, src_lang_id: str, dst_lang_id: str):
    qs = Dictionary.objects.for_user(user)
    dictionary = qs.filter(id=dict_id).first()
    src_lang = Language.objects.filter(id=src_lang_id).first()
    dst_lang = Language.objects.filter(id=dst_lang_id).first()

    if dictionary and src_lang and dst_lang:
        responses.dict_contents(
            dictionary, offset=str_to_int(offset), count=str_to_int(count), src_lang=src_lang, dst_lang=dst_lang
        ).replace_prev(callback)
    else:
        responses.dict_list(qs, text=_('Language or dictionary not found.')).replace_prev(callback)


@CallbackHandler
def delete_dictionary_request(callback: CallbackQuery, user: User, dict_id: str):
    qs = Dictionary.objects.for_user(user)
    dictionary = qs.filter(id=dict_id).first()
    if dictionary and user.has_perm('delete_dictionary', dictionary):
        responses.delete_dictionary_request(dictionary).replace_prev(callback)
    else:
        responses.dict_list(qs, text=_('Dictionary not found.')).replace_prev(callback)


@CallbackHandler
def dict_delete_confirm(callback: CallbackQuery, user: User, dict_id: str):
    qs = Dictionary.objects.for_user(user)
    dictionary = qs.filter(id=dict_id).first()
    if dictionary and user.has_perm('delete_dictionary', dictionary):
        dictionary.delete()
        text = _('Dictionary deleted.')
    else:
        text = _('Dictionary not found.')
    responses.dict_list(qs, text=text).replace_prev(callback)


@CallbackHandler
def dict_training(callback: CallbackQuery, user: User, dict_id: str, src_lang_id: str, dst_lang_id: str):
    qs = Dictionary.objects.for_user(user)
    dictionary = qs.filter(id=dict_id).first()
    src_lang = Language.objects.filter(id=src_lang_id).first()
    dst_lang = Language.objects.filter(id=dst_lang_id).first()

    if dictionary and src_lang and dst_lang:
        DictionaryUserStat.objects.get_training_stat_for_user(dictionary, user).delete()

        responses.training(user, dictionary, src_lang, dst_lang).answer_to_callback(callback)
    else:
        responses.dict_list(qs, text=_('Language or dictionary not found.')).replace_prev(callback)


@CallbackHandler
def dict_training_phrase(callback: CallbackQuery, user: User, dict_id: str, phrase_id: str, dst_lang_id: str, is_guessed: str):
    qs = Dictionary.objects.for_user(user)
    dictionary = qs.filter(id=dict_id).first()
    phrase = Phrase.objects.filter(id=phrase_id, phrase_groups__dictionaries=dictionary).first()
    dst_lang = Language.objects.filter(id=dst_lang_id).first()

    if not (dictionary and phrase and dst_lang):
        return responses.dict_list(qs, text=_('Language or phrase not found.')).replace_prev(callback)

    phrase.guessed_or_not(user, dictionary, int(is_guessed))

    # убираем клавиатуру в предыдущем сообщении и показываем перевод
    bot.edit_message_text(
        phrase.verbose_translations(dst_lang),
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
    )

    stats = dictionary.get_user_training_stats(user)
    if stats.is_training_completed(phrase.lang, dst_lang):
        responses.training_done(stats).answer_to_callback(callback)
    else:
        responses.training(user, dictionary, phrase.lang, dst_lang).answer_to_callback(callback)


@CallbackHandler
def training_done(callback: CallbackQuery, user: User, dict_id: str):
    qs = Dictionary.objects.for_user(user)
    dictionary = qs.filter(id=dict_id).first()

    if not dictionary:
        return responses.dict_list(qs, text=_('Dictionary not found.')).answer_to_callback(callback)

    stats = dictionary.get_user_training_stats(user)
    responses.training_done(stats).answer_to_callback(callback)


@bot.message_handler(content_types=['text'])
def answer(msg: Message):
    user = get_user(msg, update_state=False)

    if user.tg.state == USER_STATES.wait_input__create_dict:
        responses.create_dictionary(user, msg.text).answer_to(msg)
    elif ' - ' in msg.text:
        responses.add_phrase_groups(user, msg).answer_to(msg)
    else:
        responses.commands_list(_('Unknown command.')).answer_to(msg)


@bot.edited_message_handler()
def edit(msg: Message):
    user = get_user(msg, update_state=False)
    resp = responses.replace_phrase_groups(user, msg)
    if resp.text:
        resp.answer_to(msg)
