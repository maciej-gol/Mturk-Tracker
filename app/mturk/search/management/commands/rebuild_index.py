from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """ The rebuild_index command exists in order to disable built-in haystack
        command. The django-sphinxdoc application uses this command under the
        hood and out of control, what clears index at end of each deployment.
    """

    def handle(self, *args, **kwargs):
        pass
