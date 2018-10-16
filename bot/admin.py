from django.contrib import admin

from .models import TelegramProfile, TelegramLogEntry


@admin.register(TelegramProfile)
class TelegramProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user')
    search_fields = ['id', 'user']


@admin.register(TelegramLogEntry)
class TelegramLogEntryAdmin(admin.ModelAdmin):
    list_display = ('profile', 'text', 'response', 'timestamp', 'version')
    list_filter = ('profile',)
    search_fields = ['id', 'profile', 'text', 'response']
