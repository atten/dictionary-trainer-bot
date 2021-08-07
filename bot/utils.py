from collections import namedtuple
from inspect import signature
import re

from django.db import transaction
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.utils.encoding import force_text
from telebot.types import Message, InlineKeyboardButton, CallbackQuery

from bot import bot
from bot.commands import COMMANDS
from bot.models import TelegramProfile, USER_STATES


CALLBACK_FUNC_HANDLERS = {}


class CallbackHandler:

    def __init__(self, func_handler: callable):
        func_params = list(signature(func_handler).parameters.keys())
        field_names = func_params[2:] if len(func_params) > 2 else ['empty']
        name = func_handler.__name__
        self.t = namedtuple(name, field_names=field_names)

        CALLBACK_FUNC_HANDLERS[name] = func_handler

    def __call__(self, label, *args, **kwargs):
        return self.mk_button(label, *args, **kwargs)

    def mk_button(self, label, *args, **kwargs):
        if args or kwargs:
            d = self.t(*args, **kwargs)
            callback_data = ':'.join([self.t.__name__] + list(map(str, d)))
        else:
            callback_data = self.t.__name__

        return InlineKeyboardButton(force_text(label), callback_data=callback_data)


@bot.callback_query_handler(func=lambda x: True)
def callback_dispatcher(callback: CallbackQuery):
    parts = callback.data.split(':')
    callback_name = parts[0]
    user = get_user(callback.message)

    if len(parts) > 1:
        args = parts[1:]
    else:
        args = ()

    CALLBACK_FUNC_HANDLERS[callback_name](callback, user, *args)


def get_unique_username(username: str) -> str:
    """
    Если username существует, пробует добавить в конец 5 рандомных символов латинницы,
    укладываясь по длине в 150 симв.
    """
    username = username or 'undefined'
    while 1:
        if User.objects.filter(username=username).exists():
            username = username[:145] + get_random_string(5)
        else:
            return username


def update_user_state(profile: TelegramProfile, msg: Message):
    if msg.text == COMMANDS.create_dict:
        profile.set_state(USER_STATES.wait_input__create_dict)
    else:
        profile.reset_state()


def get_user(msg: Message, update_state: bool = True) -> User:
    from_user = msg.chat
    try:
        user = User.objects.get(tg=from_user.id)
        profile = user.tg
    except User.DoesNotExist:
        with transaction.atomic():
            user = User(
                username=get_unique_username(from_user.username),
                first_name=from_user.first_name or '',
                last_name=from_user.last_name or '',
            )
            user.set_unusable_password()
            user.save()

            profile = TelegramProfile.objects.create(
                id=from_user.id,
                user=user,
            )

    if update_state:
        update_user_state(profile, msg)
    return user


def str_to_int(s):
    """
    Гарантированно вернёт число из строки.
    """
    if s is None:
        return 0
    try:
        return int(s)
    except ValueError:
        nums = re.findall(r'\d+', s)
        return int(nums[0]) if len(nums) else 0


def fix_input_uppercase(line: str) -> str:
    """
    Убирает верхний регистр первого символа, если это единственный символ в строке в верхнем регистре.
    Полезно для ввода с телефонов.

    'abc' -> 'abc'
    'Abc' -> 'abc'
    'ABC' -> 'ABC'
    """
    if not line:
        return line

    has_uppercase_after = any(map(lambda x: x.isupper(), line[1:]))
    if has_uppercase_after:
        return line

    return line[0].lower() + line[1:]
