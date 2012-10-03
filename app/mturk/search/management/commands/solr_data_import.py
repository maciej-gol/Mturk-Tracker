import logging
import time
import urllib2
import resource

from datetime import datetime, timedelta
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand

from mturk.main.models import IndexQueue
from solr_status import SolrStatusParser


# Set limit for avaliable resources.
resource.setrlimit(resource.RLIMIT_AS, (2048 * 1048576L, -1L))
logger = logging.getLogger(__name__)

class SolrDataImportCommand(BaseCommand):

    FULL_IMPORT = "full-import"
    DELTA_IMPORT = "delta-import"

    INDEX_QUEUE_BATCH_SIZE = 1000

    option_list = BaseCommand.option_list + (
        make_option("--verbose", dest="verbose", action="store_true",
                    default=False, help=u"print more messages"),
        make_option("--import-type", dest="import_type", action="store",
                    choices=(FULL_IMPORT, DELTA_IMPORT), default=FULL_IMPORT,
                    help=u"specifies which import command should be used"),
        make_option("--clean-index", dest="clean_index", action="store_true",
                    default=False, help=u"specifies wheter to clean up index "
                    "before the indexing is started"),
        make_option("--clean-queue", dest="clean_queue", action="store_true",
                    default=False, help=u"specifies wheter to clear index "
                    "queue before the indexing is started"),
        make_option("--older-than", dest="older_than", type="int", default=2,
                    help=u"specifies which rows in the index queue will be "
                    "removed"),
    )

    def handle(self, *args, **options):

        clean_index = str(options["clean_index"]).lower()
        command = str(options["import_type"]).lower()
        import_url = "{}/data_import?command={}&clean={}"\
                     .format(settings.SOLR_PATH, command, clean_index)
        clean_queue = options["clean_queue"]
        if clean_queue:
            days = options["older_than"]
            now = datetime.now()
            older_than = now - timedelta(days=days)
            logger.info("Removing rows from the index queue older than {}"
                        .format(older_than))
            IndexQueue.objects.filter(created__lte=older_than).delete()
            logger.info("Removed")

        logger.info("Building solr index started")
        response = urllib2.urlopen(import_url)
        status_url = "{}/import_db_hits?command=status".format(settings.SOLR_PATH)
        if options["verbose"]:
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
