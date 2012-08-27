# -*- coding: utf-8 -*-

from utils.management.commands.base.db_procedure_command import DBProcedureCommand
import logging


class Command(DBProcedureCommand):
    help = ('Updates hits_mv hits_posted and hits_consumed using date from'
        ' hits_temp.')
    proc_name = 'hits_update'
    logger = logging.getLogger('mturk.arrivals.db_hits_update')
