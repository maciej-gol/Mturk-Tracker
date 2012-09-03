# -*- coding: utf-8 -*-

from utils.management.commands.base.db_procedure_command import DBProcedureCommand
import logging


class Command(DBProcedureCommand):
    help = ('Populates crawagrefates hits_posted and hits_consumed based on '
        'hits_mv records.')
    proc_name = 'reward_population'
    logger = logging.getLogger('mturk.arrivals.db_reward_population')
