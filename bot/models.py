from django.contrib.auth.models import User
from django.db import models
from django.db.models import SET_NULL, CASCADE
from django.utils.translation import ugettext_lazy as _

from model_utils import Choices
from model_utils.models import TimeStampedModel

import dictrainer

USER_STATES = Choices(
    'wait_nothing',
    'wait_input__create_dict',
)


class TelegramProfile(models.Model):
    user = models.OneToOneField(User, on_delete=CASCADE, related_name='tg')
    state = models.CharField(choices=USER_STATES, default=USER_STATES.wait_nothing, max_length=64)
    current_dict = models.ForeignKey('dictionary.Dictionary', blank=True, null=True, on_delete=SET_NULL)

    class Meta:
        verbose_name = _('Profile')
        verbose_name_plural = _('Profiles')

    def __str__(self):
        return str(self.user)

    def set_state(self, state: str, save=True):
        if self.state != state:
            self.state = state
            if save:
                self.save()

    def reset_state(self, save=True):
        self.set_state(USER_STATES.wait_nothing, save)


class TelegramLogEntry(models.Model):
    profile = models.ForeignKey(TelegramProfile, on_delete=CASCADE, related_name='logs')
    text = models.TextField(help_text=_('Message from user'), max_length=128)
    response = models.CharField(help_text=_('Response to user'), max_length=128)
    version = models.CharField(max_length=64, default=dictrainer.__version__, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Log entry')
        verbose_name_plural = _('Log entries')

    def __str__(self):
        return _('LogEntry #{0}').format(self.id)


class TelegramMessageEntity(models.Model):
    chat_id = models.IntegerField()
    message_id = models.IntegerField()
    phrases = models.ManyToManyField('dictionary.Phrase', related_name='messages')

    class Meta:
        unique_together = [
            ['chat_id', 'message_id']
        ]

        index_together = [
            ['chat_id', 'message_id']
        ]

        verbose_name = _('Message-related entity')
        verbose_name_plural = _('Message-related entities')
