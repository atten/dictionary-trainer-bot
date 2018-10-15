from django.contrib import admin
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from .models import Language, Phrase, PhraseAlias, Dictionary


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'code_aliases', 'priority')
    search_fields = ['name', 'code', 'code_aliases']


@admin.register(Phrase)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('lang', 'user', 'text')
    autocomplete_fields = ['lang', 'user']


@admin.register(PhraseAlias)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('id', 'user')
    autocomplete_fields = ['user']


@admin.register(Dictionary)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name', 'user',)
    autocomplete_fields = ['user']
