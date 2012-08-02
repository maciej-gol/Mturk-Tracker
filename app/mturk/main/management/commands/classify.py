import json
import logging
import resource

from optparse import make_option
from django.core.management.base import BaseCommand

from mturk.main.models import HitGroupClass
from mturk.main.classification import NaiveBayesClassifier

from utils.sql import query_to_dicts


# Set limit for avaliable resources.
resource.setrlimit(resource.RLIMIT_AS, (2048 * 1048576L, -1L))
logger = logging.getLogger(__name__)

class ClassifyCommand(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option("--input-path", dest="input_path", action="store",
                    help=u"classifier path"),
        make_option("--group-id", dest="group_id", action="store",
                    help=u"group id"),
        make_option("--update", dest="group_id", action="store_true",
                    default=False),
    )


    def handle(self, *args, **options):
        with open(options["input_path"], "r") as file:
            probabilities = json.load(file)
            classifier = NaiveBayesClassifier(probabilities=probabilities)
            models = query_to_dicts(
                """ SELECT group_id, title, description, keywords
                    FROM main_hitgroupcontent as content
                    WHERE NOT EXISTS(
                        SELECT * FROM main_hitgroupclass as class
                        WHERE content.group_id = class.group_id
                    ) LIMIT 100;
                """)
        def _to_hit_group_class(results):
            for result in results:
                doc = result["document"]
                prob = result["probabilities"]
                _compare = lambda k1, k2: k1 if prob[k1] > prob[k2] else k2
                yield HitGroupClass(group_id=doc["group_id"],
                                    classes=reduce(_compare, prob),
                                    probabilities=json.dumps(prob))
        results = _to_hit_group_class(classifier.classify_batch(models))
        HitGroupClass.objects.bulk_create(results)


Command = ClassifyCommand
