from django.contrib import admin

from .models import TelegramProfile, TelegramLogEntry, TelegramMessageEntity


@admin.register(TelegramProfile)
class TelegramProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created', 'last_action_dt')
    search_fields = ['id', 'user']


@admin.register(TelegramLogEntry)
class TelegramLogEntryAdmin(admin.ModelAdmin):
    list_display = ('profile', 'text', 'text_length', 'response', 'timestamp', 'version')
    list_filter = ('profile',)
    search_fields = ['id', 'profile', 'text', 'response']


@admin.register(TelegramMessageEntity)
class TelegramMessageEntityAdmin(admin.ModelAdmin):
    list_display = ('chat_id', 'message_id')
    autocomplete_fields = ['phrases']
