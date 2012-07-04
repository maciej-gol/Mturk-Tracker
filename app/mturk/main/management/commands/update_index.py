from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """ The update_index command exists in order to disable built-in haystack
        command. """

    def handle(self, *args, **kwargs):
        pass
