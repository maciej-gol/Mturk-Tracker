import json
import logging
import resource
import sys

from optparse import make_option
from django.core.management.base import BaseCommand

from mturk.main.models import HitGroupContent
from mturk.classification import NaiveBayesClassifier


# Set limit for avaliable resources.
resource.setrlimit(resource.RLIMIT_AS, (2048 * 1048576L, -1L))
logger = logging.getLogger(__name__)

class TrainCommand(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option("--input-path", dest="input_path", action="store",
                    help=u"trainig json data path"),
        make_option("--output-path", dest="output_path", action="store",
                    default="",
                    help=u"trainig json data path"),
        make_option("--display", dest="display", action="store_true",
                    default=False,
                    help=u"only displays training set and exits"),
        make_option("--load", dest="load", action="store_true",
                    default=True,
                    help=u"input file contains only primary keys, fetch "
                    "documents from the database"),
    )

    def handle(self, *args, **options):

        objects = []
        with open(options['input_path'], "r") as file:
            objects = json.load(file)

        models = HitGroupContent.objects.filter(group_id__in=objects)
        training_set = map(lambda m: (m, objects[m.group_id]), models)

        if options["display"]:
            for test in training_set:
                model = test[0]
                print model.group_id, test[1]
                print "\t{}\n\t{}\n\t{}\n\t{}".format(model.title,
                                                      model.description,
                                                      model.requester_name,
                                                      model.keywords)
        else:
            classifier = NaiveBayesClassifier(training_set=training_set)
            output_path = options["output_path"]
            if output_path:
                with open(options["output_path"], "w") as file:
                    json.dump(classifier.probabilities, file,
                              ensure_ascii=True, indent=4)
            else:
                json.dump(classifier.probabilities, sys.stdout,
                          ensure_ascii=True, indent=4)


Command = TrainCommand
