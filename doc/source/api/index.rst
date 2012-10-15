Mturk-Tracker Web Api
=====================

Data gathered by Mturk-Tracker can be accessed directly - using our wep api.
This document describes the available resources and briefly presents methods
of retrieving the data.


Available data
--------------

Currently, the api offers the following endpoints:

* `HIT group content <http://mturk-tracker.com/api/hitgroupcontent/schema/?format=json>`_

Data offered depends on whether our crawler can access the group via it's
direct url address (https://www.mturk.com/mturk/preview?groupId=<group_id>).

Data available at all times relates to what was is available on the group
listing, this is: title, description, requester, expiration date,
time allotted, reward, keywords, qualifications and date posted (when was
the first time our crawler has downloaded this group).

If the direct url can be accessed, meaning the group was public and did not
require some special qualifications, the HIT group's content may also be
available.

Url: http://mturk-tracker.com/api/hitgroupcontent/schema/?format=json

* `HIT group status  <http://mturk-tracker.com/api/hitgroupstatus/schema/?format=json>`_

Contains the information of how many hits were available for a given group
in the give time. Available data: hits_available (the current status),
crawl_date (date + time), group_id,  hit_expiration_date and
hit_group_content_id (allows querying on database id's instead of mturk's
group_id that is a string).

Url: http://mturk-tracker.com/api/hitgroupstatus/schema/?format=json


Using the api
=============

Django-tastypie
---------------

Internally, we are using `django-tastypie <http://django-tastypie.readthedocs.org/en/latest/>`_
to create our api. Following is a short guide on the structure and use of the
api, when in doubt, consult django-tastypie's documentation.


Api Endpoints
-------------

Each endpoint consists of two urls:

* the resource, located at /api/<resource_name>/
* resource schema, located at /api/<resource_name>/schema/

See schema for endpoint's most up to date documentation.


Important - limit your requests
-------------------------------

Since querying large datasets may take longer than the request response cycle is
allowed on the server, when experiencing '504 Gateway Time-out' errors please
try reducing the amount of data queried in a single batch and retry.

Moreover, when using paging, make sure to have the data ordered to be able to
retrieve the complete data in disjoin chunks.


Brief api introduction
----------------------

Before performing any queries, navigate to one of the resource's schema url to
see it's description.

Resource schema lists all available fields along with their types. Fields that
can be used a query parameters are contained in filtering and ordering lists.


Ordering and filtering the data
-------------------------------
Introduction to querying in django-tastypie is included in it's
`documentation <http://django-tastypie.readthedocs.org/en/v0.9.11/interacting.html#getting-a-collection-of-resources>`_.

The api query parameters use a similar notation to
`django orm field lookup <https://docs.djangoproject.com/en/dev/ref/models/querysets/#field-lookups>`_,
this is:

    <field_name>__<lookup_operator>=value

for example:

    crawl_date__gt=2012-10-15


    crawl_date__lt=2012-10-25


    group_id__iexact=2E3PVP3TVOK55ILV6CYQKOZK0ST14E

and for ordering:

    order_by=<field_name>

for example:

    order_by=title


    order_by=crawl_date

See an `example query <http://mturk-tracker.com/api/hitgroupstatus/?format=json&order_by=crawl_date&group_id=2E3PVP3TVOK55ILV6CYQKOZK0ST14E&crawl_date__gt=2012-10-03&crawl_date__lt=2012-10-04>`_
for getting statuses of some HIT group over a given period of time.
