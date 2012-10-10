"""Module for easy procedures development and deployment.

Use the following to define what should be created:
PROCEDURES_TO_CREATE, EXTRA_COLUMNS, EXTRA_TABLES.

"""
import os
from django.db import transaction
from utils.sql import (execute_sql, get_table_columns, add_table_columns,
    table_exists)

SQL_PATH = os.path.abspath(os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'management', 'commands', 'sql'))

import logging

log = logging.getLogger(__name__)


def create_all():
    """Creates procedures, extra tables and columns."""
    __create_procedures()
    __create_extra_columns()
    __create_extra_tables()


def __create_procedures():
    """Executes create or replace for each procedure mentioned in
    PROCEDURES_TO_CREATE.

    Each procedure is defined by a filename and a procedure creating function.
    Filename with extension stripped will be the new procedure's name and the
    file's content it's body.

    The create function should take procedure's name and the content of it's
    file. Simplest such function is create_no_args which simply wraps procedure
    code in a correct CREATE OR REPLACE FUNCTION statement.

    """
    sqls = []
    for prfile, method in PROCEDURES_TO_CREATE.iteritems():
        prname = os.path.splitext(os.path.basename(prfile))[0]
        sqlpath = os.path.join(SQL_PATH, prfile)
        log.info('Creating procedure {prname} from file: {sqlpath}'.format(
            prname=prname, sqlpath=sqlpath))
        sqls.append(method(prname, open(sqlpath).read()))
    execute_sql('\n'.join(sqls))
    transaction.commit_unless_managed()


def __create_extra_tables():
    """No automation here, just add lines for extra tables wanted."""
    for table_name, table_sql in EXTRA_TABLES.iteritems():
        path = os.path.join(SQL_PATH, table_sql)
        if table_exists(table_name):
            log.warning('Table {0} exists.'.format(table_name))
        else:
            execute_sql(open(path).read())
            log.info('Creating table {0}.'.format(table_name))
    transaction.commit_unless_managed()


def __create_extra_columns():
    """Adds extra columns if they are not present, logging a warning should the
    column exist with a different database field type.mro

    """
    for tablename, cols in EXTRA_COLUMNS.iteritems():
        if len(cols) == 0:
            log.warning('No columns in the create list for {0}.'.format(
                tablename))
            continue

        to_create = []
        ecols = get_table_columns(tablename, with_data_type=True)
        for (colname, coltype) in cols:
            if colname in ecols:
                # compare datatype name
                if coltype != ecols[colname]:
                    log.error("Column exists, but has a different type!")
                log.warning("Column already exists, not creating.")
            else:
                log.info("Creating column {0} ({1}) on {2}.".format(
                    colname, coltype, tablename))
                to_create.append((colname, coltype))
        add_table_columns(tablename, to_create)


def proc_create_query(prname, prtext, argslist=None):
    """Base method for creating procedure with given name, body and args."""
    prtext = prtext.replace("'", "''")
    TEMPLATE = """
    CREATE OR REPLACE FUNCTION {prname}({argstext}) RETURNS VOID AS'
        {prtext}'
    LANGUAGE plpgsql;
    """
    argstext = ", ".join(argslist) if argslist else ''
    return TEMPLATE.format(prname=prname, prtext=prtext, argstext=argstext)


def create_no_args(prname, prtext):
    return proc_create_query(prname, prtext)


def create_with_date_args(prname, prtext):
    argslist = [
        "istart TIMESTAMP WITH TIME ZONE",
        "iend TIMESTAMP WITH TIME ZONE",
    ]
    return proc_create_query(prname, prtext, argslist)


def create_with_date_and_threshold_args(prname, prtext):
    argslist = [
        "istart TIMESTAMP WITH TIME ZONE",
        "iend TIMESTAMP WITH TIME ZONE",
        "crawl_threshold REAL",
    ]
    return proc_create_query(prname, prtext, argslist)

"""Dictionary {procedure_file_name.sql: procedure_creting_method}.
See __create_procedures for more details.

"""
PROCEDURES_TO_CREATE = {
    'hits_temp_population.sql': create_with_date_and_threshold_args,
    'hits_update.sql': create_with_date_args,
    'initial_post_hits_update.sql': create_with_date_args,
    'reward_population.sql': create_with_date_args,
}

"""Extra columns to create. {table_name: [(colname, type), ]}."""
EXTRA_COLUMNS = {
    u"hits_mv": [
        (u"hits_posted", u"integer"),
        (u"hits_consumed", u"integer"),
    ],

    # Those columns will be added using django orm, as they are on an existing
    # model
    #
    # u"main_crawagregates": [
    #     (u"hitgroups_posted", "integer"),
    #     (u"hitgroups_consumed", "integer"),
    #     (u"rewards_posted", "double precision")
    #     (u"rewards_consumed", "double precision")
    # ]
}

"""Extra tables to create, the key will be used to verify table existence, the
value should contain sql required to create the table.
"""
EXTRA_TABLES = {
    u"hits_temp": "schema_hits_temp.sql",
}
