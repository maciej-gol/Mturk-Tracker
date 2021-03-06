Stored procedures
=================

hits_temp_population (main_hitgroupstatus -> hits_temp, main_crawlaggregates)
    selects rows from main_crawls comming from the last week (7 days), excluding
    today and:
    * inserts hits_temp record
    * updates main_crawlagregates hitgroups_posted and hitgroups_consumed as
    the count of new groups present or old groups missing respectively

hits_update (hits_temp -> hits_mv)
    updates hits_mv hits_posted or hits_consumed using the data in hits_temp
    table (mapping 'signed' field hits_temp.hits into positive hits_posted and
    hits_consumed)

reward_population (hits_mv -> main_crawlagregates)
    calculates the total reward posted and consumed for each crawl from the last
    day that has a record in hits_mv and updates related main_crawlagregates
    record.

hits_column_population_daily (main_hitgroupstatus -> main_hitgroupstatus)
    calculates the following between two most recent crawls and populates fields
    of main_hitgroupstatus:
    * hits_consumed hits_arrived as the difference in hits_available for each
    group found in the crawls, taking 0 if found only in one of the adjacent
    crawls
    * projects_arrived, projects_completed a the count of new groups present,
    or existing groups missing respectively

    .. note::

        Requires extra fields on main_hitgroupstatus, which are not used by any
        further procedures. This procedure will be skipped, but remains here,
        should is be required later.

Dependencies
------------

Stored procedures should be ran in the following order:

1) hits_temp_population
2) hits_update
3) reward_population

Running
-------

All the above procedures accept two compulsory date arguments:

*``start``
*``end``

All crawls between the first of start day and last on the end day will be
processed.

.. note::

    Both ``start`` and ``end`` must have at least one crawl done that day for
    process to start.

Stored procedures can be executed from database shell (psql) by running:

    select * from <procedure_name>(start, end)

for example calling:

    select * from hits_temp_population('2012-05-01', '2012-06-01');
    select * from hits_update('2012-05-01', '2012-06-01');
    select * from reward_population('2012-05-01', '2012-06-01');

An alternative is to launch those procedures from dedicated django management
commands. Each command has it counterpart named after the procedure name, with
``'db_'`` prefix, for example: db_hits_temp_population.

See (#TODO link to crawls.rst) for more details on running django management
commands locally and on the host environment.

Database modifications
======================

A number of new columns and a table were aded to support the stored procedures.
Those objects tables can be created using
mturk.main.migration_extra.procedures.create_all function.
That methods is by default ran as a part of 0003 migration for mturk.main,
which enchances the CrawlAggregates models stored in main_crawlagregates table.

Extra columns
-------------

hits_mv
~~~~~~~

Columns

+----------------+----------+--------------+
|    Column      | Type     | Updated by   |
+================+==========+==============+
| hits_posted    | integer  | hits_update  |
+----------------+----------+--------------+
| hits_consumed  | integer  | hits_update  |
+----------------+----------+--------------+

Indexes:

+------------------------------+-------+-------------------------------------+
| Name                         | Type  | Target                              |
+==============================+=======+=====================================+
| groupid_crawlid_hitsposted   | btree | (group_id, crawl_id, hits_posted)   |
+------------------------------+-------+-------------------------------------+
| groupid_crawlid_hitsconsumed | btree | (group_id, crawl_id, hits_consumed) |
+------------------------------+-------+-------------------------------------+

main_crawlagregates
~~~~~~~~~~~~~~~~~~~

Columns


+---------------------+-------------------+-----------------------+
|    Column           | Type              | Updated by            |
+=====================+===================+=======================+
| rewards_posted      | double precision  | reward_population     |
+---------------------+-------------------+-----------------------+
| rewards_consumed    | double precision  | reward_population     |
+---------------------+-------------------+-----------------------+
| hitgroups_posted    | integer           | hits_temp_population  |
+---------------------+-------------------+-----------------------+
| hitgroups_consumed  | integer           | hits_temp_population  |
+---------------------+-------------------+-----------------------+

Indexes:

+-------------------------+-------+------------------------------+
| Name                    | Type  | Target                       |
+=========================+=======+==============================+
| crawlid_rewardsconsumed | btree | (crawl_id, rewards_posted)   |
+-------------------------+-------+------------------------------+
| crawlid_rewardsposted   | btree | (crawl_id, rewards_consumed) |
+-------------------------+-------+------------------------------+

hits_temp table
---------------

An intermediate table for calculating hits difference between two crawls for a
single group. Columns: group_id1 and group_id2 are used to discover hit group
arrivals and disappearances.

+---------------+-----------------------+
|    Column     |         Type          |
+===============+=======================+
| hits          | integer               |
+---------------+-----------------------+
| group_id1     | character varying(50) |
+---------------+-----------------------+
| group_id2     | character varying(50) |
+---------------+-----------------------+
| crawl_id      | integer               |
+---------------+-----------------------+
| prev_crawl_id | integer               |
+---------------+-----------------------+

Indexes:

+-------------------------+-------+---------------------------------+
| Name                    | Type  | Target                          |
+=========================+=======+=================================+
| onhits                  | btree | (hits)                          |
+-------------------------+-------+---------------------------------+
| onhits_grpid2_crawlid   | btree | (group_id2, crawl_id, hits)     |
+-------------------------+-------+---------------------------------+
| onhits_grpid2_pcrawlid  | btree | (group_id2, prev_crawl_id, hits)|
+-------------------------+-------+---------------------------------+
| onhits_grpid_crawlid    | btree | (group_id1, crawl_id, hits)     |
+-------------------------+-------+---------------------------------+
| onhits_grpid_pcrawlid   | btree | (group_id1, prev_crawl_id, hits)|
+-------------------------+-------+---------------------------------+

main_hitgroupstatus (hits_column_populate_daily)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::

    UNUSED, theese modifications were NOT introduced as they are required only
    by hits_column_population_daily which is currently unused.

+---------------------+----------+-------------------------------+
|    Column           | Type     | Updated by                    |
+=====================+==========+===============================+
| projects_arrived    | integer  | hits_column_population_daily  |
+---------------------+----------+-------------------------------+
| projects_completed  | integer  | hits_column_population_daily  |
+---------------------+----------+-------------------------------+
| hits_arrived        | integer  | hits_column_population_daily  |
+---------------------+----------+-------------------------------+
| hits_consumed       | integer  | hits_column_population_daily  |
+---------------------+----------+-------------------------------+

Development
===========

To speed up development, a number of handy methods were created,
see (#TODO link to) mturk/main/migration_extra/procedures.py).

This module can be used to easily create database functions and required tables
or table columns.
