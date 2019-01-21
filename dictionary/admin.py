from django.contrib import admin

from .models import Language, Phrase, PhraseGroup, Dictionary, PhraseUserStat, DictionaryUserStat


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'code_aliases', 'priority')
    search_fields = ['name', 'code', 'code_aliases']


@admin.register(Phrase)
class PhraseAdmin(admin.ModelAdmin):
    list_display = ('lang', 'user', 'text', 'created', 'modified')
    autocomplete_fields = ['lang', 'user']
    list_filter = ('user',)
    search_fields = ['text']
    ordering = ['-id']


@admin.register(PhraseGroup)
class PhraseGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created', 'modified')
    autocomplete_fields = ['user', 'dictionaries', 'phrases']
    ordering = ['-id']


@admin.register(Dictionary)
class DictionaryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created', 'modified')
    autocomplete_fields = ['user', 'editors', 'viewers']
    search_fields = ['name']
    ordering = ['-id']


@admin.register(PhraseUserStat)
class PhraseUserStatAdmin(admin.ModelAdmin):
    list_display = ('user', 'phrase', 'trained_count', 'guessed_count', 'guessed_ratio')
    autocomplete_fields = ['user', 'phrase']
    search_fields = ['user', 'phrase']
    ordering = ['-modified']


@admin.register(DictionaryUserStat)
class DictionaryUserStatAdmin(admin.ModelAdmin):
    list_display = ('user', 'dict', 'kind', 'trained_count', 'guessed_count')
    autocomplete_fields = ['user', 'dict']
    ordering = ['-modified']
