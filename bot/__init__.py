from time import sleep

import telebot
from django_docker_helpers.utils import run_env_once

from django.conf import settings
from requests.exceptions import ReadTimeout, ConnectionError

assert settings.BOT['TOKEN'], 'BOT TOKEN unassigned!'

telebot.logger.setLevel(telebot.logging.INFO)
telebot.apihelper.proxy = settings.BOT['PROXY']
bot = telebot.TeleBot(settings.BOT['TOKEN'], threaded=settings.BOT['THREADED'])


@run_env_once
def run_bot():
    from bot import handlers    # NOQA

    while 1:
        try:
            bot.polling(non_stop=True)
        except (ReadTimeout, ConnectionError) as e:
            print(e)
            print('reconnect in 1s...')
            sleep(1)
