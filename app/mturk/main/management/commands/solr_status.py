import logging
import time
import urllib2

from xml.dom import minidom
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand

from solr_command import SolrCommand


logger = logging.getLogger(__name__)


class SolrStatusParser(object):

    STATUS_NAME = "status"
    DESCRIPTION_NAME_0 = "importResponse"
    DESCRIPTION_NAME_1 = ""
    TOTAL_ROWS_FETCHED = "Total Rows Fetched"
    TOTAL_DOCS_SKIPPED = "Total Documents Skipped"
    TOTAL_DOCS_PROCESSED = "Total Documents Processed"
    FULL_DUMP_STARTED = "Full Dump Started"
    TIME_TAKEN = "Time taken"


    RELEVANT_NAMES = [STATUS_NAME, DESCRIPTION_NAME_0, DESCRIPTION_NAME_1,
                      TOTAL_ROWS_FETCHED, TOTAL_DOCS_SKIPPED, TIME_TAKEN,
                      TOTAL_DOCS_PROCESSED, FULL_DUMP_STARTED]

    BUSY_STATUS = "busy"

    @property
    def busy(self):
        return (self.result_dict[self.STATUS_NAME] == self.BUSY_STATUS)

    def __init__(self, response):
        xml = minidom.parseString(response)
        elements = xml.getElementsByTagName("str")
        info_dict = {}
        for element in elements:
            name = element.getAttribute("name")
            if name in self.RELEVANT_NAMES:
                first_child = element.firstChild
                if first_child is not None:
                    value = first_child.toxml()
                    info_dict[name] = value
        self.result_dict = info_dict

    def __str__(self):
        return self.asstring()

    def asdict(self):
        return self.result_dict

    def asstring(self):
        result_dict = self.result_dict
        result_list = []
        for key in result_dict:
            value = result_dict[key]
            if key == "status":
                key = "Raw status"
            elif key == "":
                key = "Description"
            result_list.append("{}: {}".format(key, value))
        return "\n".join(result_list)


class SolrStatusCommand(SolrCommand):

    def handle(self, *args, **options):
        self.setup_logger(logger)
        status_url = "{}/import_db_hits?command=status".format(settings.SOLR_PATH)
        response = urllib2.urlopen(status_url)
        solr_info = SolrStatusParser(response.read())
        logger.info("Solr status:\n{}".format(solr_info))

Command = SolrStatusCommand
