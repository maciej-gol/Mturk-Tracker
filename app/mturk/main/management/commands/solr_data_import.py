import logging
import time
import urllib2
import resource

from datetime import datetime, timedelta
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand

from mturk.main.models import IndexQueue
from solr_command import SolrCommand
from solr_status import SolrStatusParser


# Set limit for avaliable resources.
resource.setrlimit(resource.RLIMIT_AS, (2048 * 1048576L, -1L))
logger = logging.getLogger(__name__)

class SolrDataImportCommand(SolrCommand):

    FULL_IMPORT = "full-import"
    DELTA_IMPORT = "delta-import"
    IMPORT_TYPES = [FULL_IMPORT, DELTA_IMPORT]
    DEFAULT_IMPORT_TYPE = FULL_IMPORT

    DEFAULT_CLEAN = False
    DEFAULT_VERBOSE = False
    DEFAULT_CLEAR_QUEUE = True

    INDEX_QUEUE_BATCH_SIZE = 1000

    option_list = BaseCommand.option_list + (
        make_option("--verbose", dest="verbose", action="store_true",
                    default=DEFAULT_VERBOSE, help=u"print more messages"),
        make_option("--import-type", dest="import_type", action="store",
                    choices=IMPORT_TYPES, default=DEFAULT_IMPORT_TYPE,
                    help=u"specifies which import command should be used"),
        make_option("--clean", dest="clean", action="store_true",
                    default=DEFAULT_CLEAN, help=u"specifies wheter to clean up "
                    "index before the indexing is started"),
        make_option("--clear-queue", dest="clear_queue", action="store_true",
                    help=u"specifies wheter to clear index queue before the "
                    "indexing is started"),
        make_option("--older-than", dest="older_than", type="int", default=2,
                    help=u"specifies which rows in the index queue will be "
                    "removed"),
    )

    def handle(self, *args, **options):
        self.setup_logger(logger)

        clean = str(options.get("clean", self.DEFAULT_CLEAN)).lower()
        command = str(options.get("import_type", self.DEFAULT_IMPORT_TYPE)).lower()
        import_url = "{}/import_db_hits?command={}&clean={}"\
                     .format(settings.SOLR_PATH, command, clean)
        clear_queue = options.get("clear_queue", self.DEFAULT_CLEAR_QUEUE)
        if clear_queue:
            days = options["older_than"]
            now = datetime.now()
            older_than = now - timedelta(days=days)
            logger.info("Removing rows from the index queue older than {}"
                        .format(older_than))
            while True:
                queryset = IndexQueue.objects.filter(created__lte=older_than)
                queryset = queryset[:self.INDEX_QUEUE_BATCH_SIZE]
                if not queryset:
                    break
                queryset.delete()
            logger.info("Removing finished")

        logger.info("Building solr index started")
        response = urllib2.urlopen(import_url)
        status_url = "{}/import_db_hits?command=status".format(settings.SOLR_PATH)
        if options.get("verbose", self.DEFAULT_VERBOSE):
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
