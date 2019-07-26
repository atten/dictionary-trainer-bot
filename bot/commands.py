from django.utils.translation import ugettext_lazy as _

from model_utils import Choices


COMMANDS = Choices(
    ('/create_dict', 'create_dict', _('Create new dictionary')),
    ('/list_dicts', 'list_dicts', _('View your dictionaries')),
    ('/dict_detail', 'dict_detail', _('View your current dictionary')),
    ('/help', 'help', _('Readme and contacts')),
)


def commands_as_text():
    return '\n'.join([f'{descr}: {key}' for (key, descr) in COMMANDS])
