import logging
import time
import urllib2

from xml.dom import minidom
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand


logger = logging.getLogger(__name__)


class Command(BaseCommand):

    FULL_IMPORT = "full-import"
    DELTA_IMPORT = "delta-import"
    IMPORT_TYPES = [FULL_IMPORT, DELTA_IMPORT]

    RELEVANT_NAMES = ["status", "importResponse",
                      "Total Rows Fetched",
                      "Total Documents Processed",
                      "Total Documents Skipped"]

    option_list = BaseCommand.option_list + (
        make_option("--verbose", dest="verbose", action="store_true"),
        make_option("--import-type", dest="import_type", action="store",
                    choices=IMPORT_TYPES, default=FULL_IMPORT),
        make_option('--clean', dest='clean', action='store_true',
                    default=False)
        # make_option('--older-than', dest='older_than', type='int', default=2),
    )

    def handle(self, *args, **options):
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - "
                                      "%(levelname)s - %(message)s")
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        clean = str(options.get("clean", False)).lower()
        command = str(options.get("import_type", self.FULL_IMPORT)).lower()
        import_url = "{}/import_db_hits?command={}&clean={}"\
                     .format(settings.SOLR_PATH, command, clean)

        logger.info("Building solr index started")
        logger.debug("Calling solr from {}".format(import_url))

        response = urllib2.urlopen(import_url)
        status_url = "{}/import_db_hits?command=status".format(settings.SOLR_PATH)

        in_progress = True
        while in_progress:
            response = urllib2.urlopen(status_url)
            xml = minidom.parseString(response.read())
            elements = xml.getElementsByTagName("str")
            info_dict = {}
            for element in elements:
                name = element.getAttribute("name")
                if name in self.RELEVANT_NAMES:
                    first_child = element.firstChild
                    if first_child is not None:
                        value = first_child.toxml()
                        if name == "status":
                            in_progress = (value == "busy")
                        else:
                            info_dict[name] = value
            info_string = ""
            for key in info_dict:
                info_string += "{}: {}\n".format(key, info_dict[key])
            logger.debug("Import status:\n{}".format(info_string))
            if in_progress:
                time.sleep(1)
