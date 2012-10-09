import datetime
import copy
import pytz

from django.core.urlresolvers import reverse

from tenclouds.crud import fields
from tenclouds.crud import resources
from tenclouds.crud.queryset import QuerySetAdapter

from reports import ToprequestersReport


class ToprequestersQuerySetAdapter(QuerySetAdapter):
    """QuerySet adapter for a python iterable of dictionaries."""

    model = None

    class Query:
        order_by = []

    def __init__(self, iterable, model=None, **extra):
        """Extending the base init to add:

        * self.query.order_by field
        * _clone
        * mute filter/exclude
        * order_by
        * __getitem__ wrapping the objects mocking pk field

        """
        self.iterable = iterable

        # saving extra for _clone operation
        self.extra = extra
        for k, v in extra.iteritems():
            setattr(self, k, v)

        self.query = ToprequestersQuerySetAdapter.Query()
        self.model = model

    def _clone(self):
        items = copy.deepcopy(self.iterable)
        return type(self)(items, **self.extra)

    def filter(self, **kwargs):
        """Currently a no-op."""
        return self

    def exclude(self, **kwargs):
        """Currently a no-op."""
        return self

    def order_by(self, *fields):
        # ordering from the least important to the most important
        for f in reversed(fields):
            rv = f.startswith('-')
            key = f[1:] if rv else f
            # XXX: dirty, but that's not so easy to fix
            # requires setting self.model, and we don't have a model now
            if any(map(lambda x: isinstance(x.get(key), datetime.datetime),
                self.iterable)):
                # date fields:
                mindate = datetime.datetime(
                    datetime.MINYEAR, 1, 1, tzinfo=pytz.UTC)
                keyfun = lambda x: x.get(key) or mindate
            else:
                keyfun = lambda x: x.get(key)
            self.iterable.sort(key=keyfun, reverse=rv)

        # used by crud to determine the ordering
        self.query.order_by = fields

        return self

    def count(self):
        return len(self.iterable)

    class QuerySetAdapterItem(dict):

        pk = None

    def __getitem__(self, val):
        """Extending data items by mocking pk required by tastypie."""
        return [ToprequestersQuerySetAdapter.QuerySetAdapterItem(a)
            for a in self.iterable[val]]


class ToprequestersResource(resources.ModelResource):
    """A resource serving toprequesters reports.

    Those reports are evaluated externally by a cron job and reside in memcache
    from where they can be queried using ToprequestersReport class.

    """
    requester_name = fields.CharField(
        attribute='requester_name', null=True, title='Requester name')
    last_posted = fields.DateTimeField(
        attribute='last_posted', null=True, title='Last posted')
    hits = fields.FloatField(attribute='hits', null=True)
    reward = fields.FloatField(attribute='reward', null=True)
    projects = fields.IntegerField(attribute='projects', null=True)

    requester_url = fields.CharField()

    class Meta:
        list_allowed_methods = ['get', ]
        fields = [
            'last_posted', 'hits', 'requester_name', 'reward', 'projects'
        ]
        # TODO: Currently only one report type is returned regardless of tab
        # need to figure out a way to make it work properly
        queryset = ToprequestersQuerySetAdapter(
            ToprequestersReport.get_report_data(
                ToprequestersReport.AVAILABLE) or [])
        per_page = [15, 50, 100]
        ordering = [
            'requester_id', 'requester_name', 'last_posted', 'hits',
            'reward', 'projects'
        ]
        default_ordering = ['-reward']

    def dehydrate(self, bundle):
        bundle = super(ToprequestersResource, self).dehydrate(bundle)
        for field_name, field_object in self.fields.items():
            # we have a dict instead of an object here
            val = bundle.obj.get(field_name)
            # use the dehydrate_* if available
            method = getattr(self, "dehydrate_%s" % field_name, None)
            if method:
                val = method(bundle)
            bundle.data[field_name] = val
        return bundle

    def dehydrate_reward(self, bundle):
        try:
            return round(bundle.obj.get('reward'), 2)
        except TypeError:
            return None
