Database tables
===============

.. djangomodellist::


| Table **hits_mv** (no model representation)

Table storing aggregation for a hit group in a crawl.

This table uses materialized view concept. Records of this table are generated
periodically (once every hour), based on crawled information. Moreover, there is
a number of procedures updating the records with more complicated aggregations
such as hits_posted and hits_consumed or is_spam.

:**Columns**: * **status_id** (integer)
              * **content_id** (integer)
              * **group_id** (varchar(50)) Index
              * **crawl_id** (integer) Index
              * **start_time** (timestamp with time zone) Index
              * **requester_id** (varchar(50))
              * **hits_available** (integer)
              * **page_number** (integer)
              * **inpage_position** (integer)
              * **hit_expiration_date** (timestamp with time zone)
              * **reward** (double precision)
              * **time_alloted** (integer)
              * **hits_diff** (integer)
              * **is_spam** (boolean) Index
              * **hits_posted** (integer)
              * **hits_consumed** (integer)


Stored procedures
=================

.. toctree::

    arrivals

Materialized views
==================

.. toctree::

    mviews
