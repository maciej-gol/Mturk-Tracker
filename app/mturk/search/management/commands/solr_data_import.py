import logging
import time
import urllib2
import resource

from datetime import datetime, timedelta
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand

from solr_status import SolrStatusParser
from utils.sql import execute_sql


# Set limit for avaliable resources.
resource.setrlimit(resource.RLIMIT_AS, (2048 * 1048576L, -1L))
logger = logging.getLogger('mturk.solr')

class SolrDataImportCommand(BaseCommand):

    FULL_IMPORT = 'full-import'
    DELTA_IMPORT = 'delta-import'

    INDEX_QUEUE_BATCH_SIZE = 1000

    option_list = BaseCommand.option_list + (
        make_option('--verbose', dest='verbose', action='store_true',
                    default=False, help=u'print more messages'),
        make_option('--import-type', dest='import_type', action='store',
                    choices=(FULL_IMPORT, DELTA_IMPORT), default=FULL_IMPORT,
                    help=u'specifies which import command should be used'),
        make_option('--clean-index', dest='clean_index', action='store_true',
                    default=False, help=u'specifies wheter to clean up index '
                    'before the indexing is started'),
        make_option('--clean-queue', dest='clean_queue', action='store_true',
                    default=False, help=u'specifies wheter to clear index '
                    'queue before the indexing is started'),
        make_option('--older-than', dest='older_than', type='int', default=2,
                    help=u'specifies which rows in the index queue will be '
                    'removed'),
    )

    def handle(self, *args, **options):
        clean_index = str(options['clean_index']).lower()
        command = str(options['import_type']).lower()
        logger.info('{} import data started'
                .format('Full' if command == self.FULL_IMPORT else 'Delta'))
        import_url = ('{}/data_import?command={}&clean={}'
                .format(settings.SOLR_PATH, command, clean_index))
        clean_queue = options['clean_queue']
        older_than = options['older_than']
        if command == self.FULL_IMPORT:
            clean_queue = True
            older_than = None
        if clean_queue:
            # Full import: truncate queue table.
            if older_than is None:
                logger.info('Removing all rows from the index queue')
                execute_sql('TRUNCATE TABLE ONLY main_indexqueue RESTRICT',
                        commit=True)
            else:
                older_than = datetime.now() - timedelta(days=older_than)
                logger.info('Removing rows older than {} from the index queue'.
                    format(older_than))
                execute_sql('''
                    DELETE
                        FROM
                            main_indexqueue
                        WHERE
                            created < '{}';
                '''.format(older_than), commit=True)

        logger.info('Building solr index')
        response = urllib2.urlopen(import_url)
        status_url = '{}/data_import?command=status'.format(settings.SOLR_PATH)
        if options['verbose']:
            in_progress = True
            while in_progress:
                response = urllib2.urlopen(status_url)
                solr_info = SolrStatusParser(response.read())
                logger.info('Solr status:\n{}'.format(solr_info))
                in_progress = solr_info.busy
                if in_progress:
                    time.sleep(1)
            logger.info('Building solr index finished')


Command = SolrDataImportCommand
