import logging
import time
import urllib2

from xml.dom import minidom
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand

from solr_command import SolrCommand
from solr_status import SolrStatusParser


logger = logging.getLogger(__name__)


class SolrDataImportCommand(SolrCommand):

    FULL_IMPORT = "full-import"
    DELTA_IMPORT = "delta-import"
    IMPORT_TYPES = [FULL_IMPORT, DELTA_IMPORT]

    option_list = BaseCommand.option_list + (
        make_option("--verbose", dest="verbose", action="store_true"),
        make_option("--import-type", dest="import_type", action="store",
                    choices=IMPORT_TYPES, default=FULL_IMPORT),
        make_option('--clean', dest='clean', action='store_true',
                    default=False)
        # make_option('--older-than', dest='older_than', type='int', default=2),
    )

    def handle(self, *args, **options):
        self.setup_logger(logger)

        clean = str(options.get("clean", False)).lower()
        command = str(options.get("import_type", self.FULL_IMPORT)).lower()
        import_url = "{}/import_db_hits?command={}&clean={}"\
                     .format(settings.SOLR_PATH, command, clean)
        logger.info("Building solr index started")
        response = urllib2.urlopen(import_url)
        status_url = "{}/import_db_hits?command=status".format(settings.SOLR_PATH)

        in_progress = True
        while in_progress:
            response = urllib2.urlopen(status_url)
            solr_info = SolrStatusParser(response.read())
            logger.info("Solr status:\n{}".format(solr_info))
            in_progress = solr_info.busy
            if in_progress:
                time.sleep(1)

        logger.info("Building solr index finished")

Command = SolrDataImportCommand
