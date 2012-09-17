# -*- coding: utf-8 -*-

from utils.management.commands.base.db_procedure_command import DBProcedureCommand
import logging


class Command(DBProcedureCommand):
    help = ('Updates hits_mv.hits_posted related to initial group posts which '
        ' are ommitted by the regular hits_update.')
    proc_name = 'initial_post_hits_update'
    logger = logging.getLogger('mturk.arrivals.db_initial_post_hits_update')
