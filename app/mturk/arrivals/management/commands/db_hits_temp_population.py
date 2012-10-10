# -*- coding: utf-8 -*-

from utils.management.commands.base.db_procedure_command import DBProcedureCommand
import logging
from django.conf import settings


class Command(DBProcedureCommand):
    help = 'Inserts rows into hits_temp table.'
    proc_name = 'hits_temp_population'
    logger = logging.getLogger('mturk.arrivals.db_hits_temp_population')

    def get_proc_args(self):
        """Adds an extra argument this procedures requires."""
        return [self.start, self.end, settings.INCOMPLETE_CRAWL_THRESHOLD]
