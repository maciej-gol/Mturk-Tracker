# -*- coding: utf-8 -*-
import time
import datetime
import logging

from optparse import make_option
from django.utils.timezone import now
from django.core.management.base import BaseCommand

from utils.sql import execute_sql
from utils.pid import Pid


log = logging.getLogger(__name__)


class SolrCommand(BaseCommand):

    def setup_logger(self, logger):
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - "
                                      "%(levelname)s - %(message)s")
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    def handle(self, *args, **options):
        raise NotImplementedError
