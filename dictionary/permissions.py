from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

from dictionary import models

UserModel = get_user_model()


DICT_VIEWER_PERMS = {
    'view_dictionary',
    'view_phrase',
    'view_phrasegroup',
}

DICT_EDITOR_PERMS = {
    'view_dictionary',
    'change_dictionary',

    'view_phrase',
    'add_phrase',
    'change_phrase',
    'delete_phrase',

    'view_phrasegroup',
    'add_phrasegroup',
    'change_phrasegroup',
    'delete_phrasegroup',
}


class DictionaryPermissionsBackend:

    def authenticate(self):
        # not supported
        pass

    def get_all_permissions(self, user_obj, obj=None):
        if not user_obj.is_active or user_obj.is_anonymous or obj is None:
            return set()

        if isinstance(obj, models.Phrase):
            is_editor = obj.phrase_groups.filter(dictionary__editors=user_obj).exists()
            is_viewer = obj.phrase_groups.filter(dictionary__viewers=user_obj).exists()
        elif isinstance(obj, models.PhraseGroup):
            is_editor = obj.dictionary.editors.filter(id=user_obj).exists()
            is_viewer = obj.dictionary.viewers.filter(id=user_obj).exists()
        elif isinstance(obj, models.Dictionary):
            is_editor = obj.editors.filter(id=user_obj.id).exists()
            is_viewer = obj.viewers.filter(id=user_obj.id).exists()
        else:
            return set()

        ret = set()
        if is_viewer:
            ret |= DICT_VIEWER_PERMS
        if is_editor:
            ret |= DICT_EDITOR_PERMS

        return ret

    def has_perm(self, user_obj, perm, obj=None):
        if not user_obj.is_active or not obj:
            return False

        if getattr(obj, 'user', None) == user_obj:
            return True

        return perm in self.get_all_permissions(user_obj, obj)
