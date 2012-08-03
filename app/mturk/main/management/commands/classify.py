import json
import logging
import resource

from optparse import make_option
from django.core.management.base import BaseCommand

from mturk.main.models import HitGroupClass, HitGroupContent
from mturk.main.classification import NaiveBayesClassifier, EmptyBatchException

from utils.sql import query_to_dicts


# Set limit for avaliable resources.
resource.setrlimit(resource.RLIMIT_AS, (2048 * 1048576L, -1L))
logger = logging.getLogger('mturk.classification')

class ClassifyCommand(BaseCommand):

    BATCH_SIZE = 1000

    option_list = BaseCommand.option_list + (
        make_option("--input-path", dest="input_path", action="store",
                    help=u"classifier path"),
        make_option("--group-id", dest="group_id", action="store",
                    default="", help=u"group id"),
        make_option("--single", dest="single", action="store_true",
                    default=False),
        make_option("--remove", dest="remove", action="store_true",
                    default=False),
    )


    def handle(self, *args, **options):
        def _to_hit_group_class(results):
            for result in results:
                doc = result["document"]
                prob = result["probabilities"]
                yield HitGroupClass(group_id=doc["group_id"],
                                    classes=NaiveBayesClassifier.most_likely(result),
                                    probabilities=json.dumps(prob))
        if options["remove"]:
            logger.info("Removing existing classification")
            HitGroupClass.objects.all().delete()
            logger.info("Classification removed")
            return
        with open(options["input_path"], "r") as file:
            probabilities = json.load(file)
            classifier = NaiveBayesClassifier(probabilities=probabilities)
            # TODO remove this -- for debug purposes only
            if options["single"] and options["group_id"]:
                model = HitGroupContent.objects.get(group_id=options['group_id'])
                print classifier.classify(model)
                return
            logger.info("Classification of hit groups started. Processing in "\
                        "batches size of {}".format(self.BATCH_SIZE))
            while True:
                models = query_to_dicts(
                    """ SELECT group_id, title, description, keywords
                        FROM main_hitgroupcontent as content
                        WHERE NOT EXISTS(
                            SELECT * FROM main_hitgroupclass as class
                            WHERE content.group_id = class.group_id
                        ) LIMIT {};
                    """.format(self.BATCH_SIZE))
                logger.info("Batch classification stated")
                try:
                    results = _to_hit_group_class(classifier.classify_batch(models))
                    HitGroupClass.objects.bulk_create(results)
                except EmptyBatchException:
                    logger.info("Batch is empty no hit groups to classify")
                    break
                logger.info("Batch classified successfully")

Command = ClassifyCommand
