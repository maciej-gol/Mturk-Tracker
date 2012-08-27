# -*- coding: utf-8 -*-

from utils.management.commands.base.db_procedure_command import DBProcedureCommand
import logging


class Command(DBProcedureCommand):
    help = 'Inserts rows into hits_temp table.'
    proc_name = 'hits_temp_population'
    logger = logging.getLogger('mturk.arrivals.db_hits_temp_population')
