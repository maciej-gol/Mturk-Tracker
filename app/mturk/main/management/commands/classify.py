import json
import logging
import resource

from optparse import make_option
from django.core.management.base import BaseCommand

from mturk.main.models import HitGroupContent
from mturk.main.classification import NaiveBayesClassifier


# Set limit for avaliable resources.
resource.setrlimit(resource.RLIMIT_AS, (2048 * 1048576L, -1L))
logger = logging.getLogger(__name__)

class ClassifyCommand(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option("--input-path", dest="input_path", action="store",
                    help=u"classifier path"),
        make_option("--group-id", dest="group_id", action="store",
                    help=u"group id"),
    )

    def handle(self, *args, **options):
        model = HitGroupContent.objects.get(group_id=options["group_id"])
        with open(options["input_path"], "r") as file:
            probabilities = json.load(file)
            classify = NaiveBayesClassifier(probabilities=probabilities)
            result = classify(model)
            print json.dumps(result, ensure_ascii=True, indent=4)

Command = ClassifyCommand
