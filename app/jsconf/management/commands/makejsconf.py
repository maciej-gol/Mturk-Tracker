import os
import logging
from django.core.management.base import BaseCommand
from django.conf import settings

from jsconf.jsconf import get_config

log = logging.getLogger(__name__)


class Command(BaseCommand):
    help = ("Generate jsconf.js file statically, to be served by the webserver"
            " as a static file. This should be run during every deploy.")

    def handle(self, **options):

        path = os.path.join(
            settings.STATIC_ROOT,
            getattr(settings, 'JSCONF_PATH', 'js/jsconf.js'))

        with open(path, "w") as f:
            f.write(get_config())

        log.info("Done: jsconf placed in: {0}.".format(path))
