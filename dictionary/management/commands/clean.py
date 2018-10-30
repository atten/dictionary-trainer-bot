from django.core.management.base import BaseCommand

from dictionary.models import PhraseGroup, Phrase


class Command(BaseCommand):

    def handle(self, *args: tuple, **options: dict):
        print('deleted orphaned groups:', PhraseGroup.objects.orphans().delete()[1].get('dictionary.PhraseGroup', 0))
        print('deleted orphaned phrases:', Phrase.objects.orphans().delete()[1].get('dictionary.Phrase', 0))
        print('deleted empty groups:', PhraseGroup.objects.empty().delete()[1].get('dictionary.PhraseGroup', 0))
