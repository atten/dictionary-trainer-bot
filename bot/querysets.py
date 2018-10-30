from django.db.models import QuerySet


class TelegramMessageEntityQuerySet(QuerySet):

    def empty(self):
        return self.filter(phrases=None)
