import json
import logging
import resource

from optparse import make_option
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand

from mturk.main.models import HitGroupClass
from mturk.classification import NaiveBayesClassifier, EmptyBatchException
from utils.sql import query_to_dicts


# Set limit for avaliable resources.
resource.setrlimit(resource.RLIMIT_AS, (2048 * 1048576L, -1L))
logger = logging.getLogger('mturk.classification')

class ClassifyCommand(BaseCommand):

    BATCH_SIZE = 1000

    option_list = BaseCommand.option_list + (
        make_option('--clear-all', dest='clear_all',
                    action='store_true', default=False,
                    help=u'clears all existing classification and exits'),
        make_option('--classifier-path', dest='classifier_path',
                    action='store', default='',
                    help=u'path to the classifier json configuration file'),
        make_option('--begin', dest='begin',
                    action='store', default='',
                    help=u'classify only those groups that were existing '
                    'in the specified time interval'),
        make_option('--end', dest='end',
                    action='store', default='',
                    help=u'classify only those groups that were existing '
                    'in the specified time interval'),
    )


    def handle(self, *args, **options):
        def _to_hit_group_class(results):
            for result in results:
                doc = result['document']
                prob = result['probabilities']
                yield HitGroupClass(group_id=doc['group_id'],
                                    classes=NaiveBayesClassifier.most_likely(result),
                                    probabilities=json.dumps(prob))
        if options['clear_all']:
            logger.info('Removing all existing classification')
            HitGroupClass.objects.all().delete()
            return
        if options['begin'] and options['end']:
            # XXX it can be slow.
            query = ''' SELECT group_id, title, description, keywords
                        FROM main_hitgroupcontent as content
                        JOIN hits_mv 
                        ON content.group_id = hits_mv.group_id
                        WHERE 
                            NOT EXISTS(
                                SELECT * FROM main_hitgroupclass as class
                                WHERE content.group_id = class.group_id
                            ) AND 
                            hits_mv.start_time >= {} AND 
                            hits_mv.start_time < {} 
                        GROUP BY group_id
                        LIMIT {};
                    '''.format(options['begin'], options['end'], self.BATCH_SIZE)
        else:
            query = ''' SELECT group_id, title, description, keywords
                        FROM main_hitgroupcontent as content
                        WHERE NOT EXISTS(
                            SELECT * FROM main_hitgroupclass as class
                            WHERE content.group_id = class.group_id
                        ) LIMIT {};
                    '''.format(self.BATCH_SIZE)
        if not options['classifier_path']:
            try:
                options['classifier_path'] = settings.CLASSIFIER_PATH
            except AttributeError:
                raise ImproperlyConfigured('Classifier path is not specified '
                                           'neither in the settings file'
                                           'nor in the command line')
        with open(options['classifier_path'], 'r') as file:
            probabilities = json.load(file)
            classifier = NaiveBayesClassifier(probabilities=probabilities)
            logger.info('Classification of hit groups started. Processing in '\
                        'batches size of {}'.format(self.BATCH_SIZE))
            while True:
                models = query_to_dicts(query)
                logger.info('Batch classification started')
                try:
                    results = _to_hit_group_class(classifier.classify_batch(models))
                    HitGroupClass.objects.bulk_create(results)
                except EmptyBatchException:
                    logger.info('Batch is empty no hit groups to classify')
                    break
                logger.info('Batch classified successfully')


Command = ClassifyCommand
