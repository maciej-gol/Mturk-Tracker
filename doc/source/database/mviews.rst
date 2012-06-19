Concept
-------

To speed up the access to crawls we are using materialised views concept.
In place of a view, evaluated each time anew, a table storing the data is used
instead. The data is created periodically in a cron job.

As there is no such feature in postgresql, we are using an implementation
proposed in the following article:
http://tech.jonathangardner.net/wiki/PostgreSQL/Materialized_Views

Modules
-------

The functionality is wrapped in mturk.main.migration_extra.views and applied
during the second migration: mturk.main.migrations.0002_extra_initial_sql.py.
