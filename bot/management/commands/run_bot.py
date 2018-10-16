from django.core.management.base import BaseCommand

from bot import run_bot


class Command(BaseCommand):
    requires_system_checks = False

    def handle(self, *args: tuple, **options: dict):
        run_bot()
