Stored procedures
=================

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

hits_temp_population (main_hitgroupstatus -> hits_temp, main_crawlaggregates)
    selects rows from main_crawls comming from the last week (7 days), excluding
    today and:
    * inserts hits_temp record
    * updates main_crawlagregates hitsgroups_posted and hitsgroups_consumed as
    the count of new groups present or old groups missing respectively

hits_update (hits_temp -> hits_mv)
    updates hits_mv hits_posted or hits_consumed using the data in hits_temp
    table (mapping 'signed' field hits_temp.hits into positive hits_posted and
    hits_consumed)

    .. note::

        There is a hardcoded limit on this, perhaps debug/development:
        'crawl_id < 105489;'

reward_population (hits_mv -> main_crawlagregates)
    calculates the total reward posted and consumed for each crawl from the last
    day that has a record in hits_mv and updates related main_crawlagregates
    record.

Dependencies
------------
Stored procedures should be ran in the following order:

1) hits_temp_population
2) hits_update
3) reward_population

Database modifications
======================

Extra columns
-------------

A number of new columns were aded to support the stored procedures.

.. todo::

    add an information on which migration adds them once there is one

hits_mv

+----------------+----------+--------------+
|    Column      | Type     | Updated by   |
+================+==========+==============+
| hits_posted    | integer  | hits_update  |
+----------------+----------+--------------+
| hits_consumed  | integer  | hits_update  |
+----------------+----------+--------------+

main_crawlagregates

+----------------------+-------------------+-----------------------+
|    Column            | Type              | Updated by            |
+======================+===================+=======================+
| rewards_posted       | double precision  | reward_population     |
+----------------------+-------------------+-----------------------+
| rewards_consumed     | double precision  | reward_population     |
+----------------------+-------------------+-----------------------+
| hitsgroups_posted    | integer           | hits_temp_population  |
+----------------------+-------------------+-----------------------+
| hitsgroups_consumed  | integer           | hits_temp_population  |
+----------------------+-------------------+-----------------------+

main_hitgroupstatus (hits_column_populate_daily)

.. note::

    UNUSED as it is not required in the process.
    See hits_column_population_daily description above for more details

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

hits_temp table
---------------

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
