import datetime
import json
import time

from itertools import chain
from collections import OrderedDict
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect
from django.views.generic.simple import direct_to_template
from django.views.decorators.cache import cache_page, never_cache
from haystack.views import SearchView

import admin
import plot

from mturk.main.forms import HitGroupContentSearchForm
from mturk.main.models import DayStats, HitGroupContent, HitGroupClass, \
                              RequesterProfile
from mturk.main.templatetags.graph import text_row_formater
from mturk.toprequesters.reports import ToprequestersReport
from mturk.classification import NaiveBayesClassifier, LABELS

from utils.sql import query_to_dicts, query_to_tuples, query_to_lists
from utils.enum import EnumMetaclass


HIT_DETAILS_COLUMNS = (
    ('date', 'Date'),
    ('number', '#HITs'),
)

ONE_DAY = 60 * 60 * 24
ONE_HOUR = 60 * 60


def data_formater(input):
    for cc in input:
        yield {
                'date': cc['start_time'],
                'row': (str(cc['hits']), str(cc['reward']),
                    str(cc['count']), str(cc['spam_projects'])),
        }


def general_tab_data_formatter(col, data):
    """Returns date and one other selected column."""
    for d in data:
        yield {'date': d['date'], 'row': (d['row'][col], )}


def date_from_str(s):
    return datetime.datetime(
        *time.strptime(s, '%m/%d/%Y')[:6])


def get_time_interval(get, ctx, encode=True, days_ago=30):
    """ Shortcut function that returns a time interval from the ``get``
        dictionary, and stores it in the ``ctx`` dictionary.
        The ``days_ago`` is a number of days from now, in case
        when the ``get`` does not contain any information. """
    if 'date_from' in get:
        date_from = date_from_str(get['date_from'])
    else:
        date_from = (datetime.date.today() - datetime.timedelta(days=days_ago))
    if 'date_to' in get:
        date_to = date_from_str(get['date_to'])
    else:
        date_to = (datetime.date.today() + datetime.timedelta(days=1))
    if encode:
        date_from_enc = date_from.strftime('%m/%d/%Y')
        date_to_enc = date_to.strftime('%m/%d/%Y')
    else:
        date_from_enc = date_from
        date_to_enc = date_to
    ctx['date_from'] = date_from_enc
    ctx['date_to'] = date_to_enc
    return date_from, date_to


#@cache_page(ONE_HOUR)
def general(request, tab_slug=None):

    tab = GeneralTabEnum.value_for_slug.get(tab_slug, GeneralTabEnum.ALL)

    ctx = {
        'multichart': tab == GeneralTabEnum.ALL,
        'columns': GeneralTabEnum.get_graph_columns(tab),
        'title': GeneralTabEnum.get_tab_title(tab),
        'current_tab': GeneralTabEnum.enum_dict[tab],
        'top_tabs': GeneralTabEnum.enum_dict.values(),
    }

    date_from, date_to = get_time_interval(request.GET, ctx, days_ago=7)

    data = data_formater(query_to_dicts('''
            SELECT reward, hits, projects as "count", spam_projects, start_time
            FROM main_crawlagregates
            WHERE start_time >= %s AND start_time <= %s
            ORDER BY start_time ASC
        ''', date_from, date_to))

    def _is_anomaly(a, others):
        mid = sum(map(lambda e: int(e['row'][0]), others)) / len(others)
        return abs(mid - int(a['row'][0])) > 7000

    def _fixer(a, others):
        val = sum(map(lambda e: int(e['row'][0]), others)) / len(others)
        a['row'] = (str(val), a['row'][1], a['row'][2], a['row'][3])
        return a

    if settings.DATASMOOTHING:
        ctx['data'] = plot.repair(list(data), _is_anomaly, _fixer, 2)
    else:
        ctx['data'] = list(data)

    ctx['data'] = GeneralTabEnum.data_set_processor[tab](ctx['data'])
    return direct_to_template(request, 'main/graphs/timeline.html', ctx)


def model_fields_formatter(fields, data):
    return tuple([str(getattr(data, f)) for f in fields])


#@cache_page(ONE_DAY)
def arrivals(request, tab_slug=None):

    tab = ArrivalsTabEnum.value_for_slug.get(tab_slug, ArrivalsTabEnum.ALL)

    ctx = {
        'multichart': False,
        'columns': ArrivalsTabEnum.get_graph_columns(tab),
        'title': ArrivalsTabEnum.get_tab_title(tab),
        'top_tabs': ArrivalsTabEnum.enum_dict.values(),
        'current_tab': ArrivalsTabEnum.enum_dict[tab],
    }

    def arrivals_data_formater(input, tab):
        for cc in input:
            yield {
                'date': cc.date,
                'row': ArrivalsTabEnum.data_set_processor[tab](cc),
            }

    date_from, date_to = get_time_interval(request.GET, ctx)
    data = DayStats.objects.filter(date__gte=date_from, date__lte=date_to)
    ctx['data'] = arrivals_data_formater(data, tab)
    return direct_to_template(request, 'main/graphs/timeline.html', ctx)


@never_cache
def top_requesters(request, tab=None):

    if request.user.is_superuser:
        return admin.top_requesters(request)

    try:
        tab = int(tab)
    except Exception:
        pass
    if tab not in ToprequestersReport.values:
        messages.warning(request, 'Unknown report type: {0}'.format(tab))
        return redirect('graphs_top_requesters',
                        tab=ToprequestersReport.values[0])

    data = ToprequestersReport.get_report_data(tab) or []

    def _top_requesters(request):
        def row_formatter(input):
            for cc in input:
                row = []
                row.append('<a href="%s">%s</a>' % (
                    reverse('requester_details',
                        kwargs={'requester_id': cc[0]}), cc[1]))
                row.append(('<a href="https://www.mturk.com/mturk/searchbar?'
                    'requesterId=%s" target="_mturk">%s</a> '
                    '(<a href="http://feed.crowdsauced.com/r/req/%s">RSS</a>)')
                           % (cc[0], cc[0], cc[0]))
                row.extend(cc[2:6])
                yield row

        columns = (
            ('string', 'Requester ID'),
            ('string', 'Requester'),
            ('number', '#Task'),
            ('number', '#HITs'),
            ('number', 'Rewards'),
            ('datetime', 'Last Posted On')
        )
        ctx = {
            'data': row_formatter(data),
            'report_meta': ToprequestersReport.get_report_meta(tab),
            'columns': columns,
            'title': 'Top-1000 Recent Requesters',
            'tab_enum': ToprequestersReport.display_names,
            'active_tab': tab
        }

        return direct_to_template(request, 'main/toprequesters.html', ctx)

    return _top_requesters(request)


def requester_details(request, requester_id):
    if request.user.is_superuser:
        return admin.requester_details(request, requester_id)

    @cache_page(ONE_DAY)
    def _requester_details(request, requester_id):
        def row_formatter(input):

            for cc in input:
                row = []
                row.append('<a href="{}">{}</a>'.format(
                           reverse('hit_group_details',
                           kwargs={'hit_group_id': cc[3]}), cc[0]))
                row.extend(cc[1:3])
                yield row

        requester_name = HitGroupContent.objects.filter(
            requester_id=requester_id).values_list(
            'requester_name', flat=True).distinct()

        if requester_name:
            requester_name = requester_name[0]
        else:
            requester_name = requester_id

        date_from = (datetime.date.today() - datetime.timedelta(days=30)) \
                    .isoformat()

        data = query_to_tuples("""
    select
        title,
        p.reward,
        p.occurrence_date,
        p.group_id
    from main_hitgroupcontent p
        LEFT JOIN main_requesterprofile r ON p.requester_id = r.requester_id
    where
        p.requester_id = '%s'
        AND coalesce(r.is_public, true) = true
        and
        p.occurrence_date > TIMESTAMP '%s';
        """ % (requester_id, date_from))

        columns = [
            ('string', 'HIT Title'),
            ('number', 'Reward'),
            ('datetime', 'Posted'),
        ]
        ctx = {
            'data': text_row_formater(row_formatter(data)),
            'columns': tuple(columns),
            'title': 'Tasks posted during last 30 days by %s' %
                     (requester_name, ),
            'requester_name': requester_name,
            'requester_id': requester_id,
            'user': request.user,
        }
        return direct_to_template(request, 'main/requester_details.html', ctx)

    return _requester_details(request, requester_id)


@never_cache
def hit_group_content(request, hit_group_id):
    """View used as an iframe source for hit_group_details."""

    try:
        hit_group = HitGroupContent.objects.get(group_id=hit_group_id)
        if RequesterProfile.objects.filter(requester_id=hit_group.requester_id,
            is_public=False):
            raise HitGroupContent.DoesNotExist()
    except HitGroupContent.DoesNotExist:
        messages.info(request, 'Hitgroup with id "{0}" was not found!'.format(
            hit_group_id))
        return redirect('haystack_search')

    params = {'hit_group': hit_group}
    return direct_to_template(request, 'main/hit_group_content.html', params)


@never_cache
def hit_group_details(request, hit_group_id):

    try:
        hit_group = HitGroupContent.objects.get(group_id=hit_group_id)
        if RequesterProfile.objects.filter(requester_id=hit_group.requester_id,
            is_public=False):
            raise HitGroupContent.DoesNotExist()
    except HitGroupContent.DoesNotExist:
        messages.info(request, 'Hitgroup with id "{0}" was not found!'.format(
            hit_group_id))
        return redirect('haystack_search')

    try:
        hit_group_class = HitGroupClass.objects.get(group_id=hit_group_id)
    except ObjectDoesNotExist:
        # TODO classification should be done on all models.
        hit_group_class = None
        try:
            with open(settings.CLASSIFIER_PATH, "r") as file:
                classifier = NaiveBayesClassifier(
                        probabilities=json.load(file)
                    )
                classified = classifier.classify(hit_group)
                most_likely = classifier.most_likely(classified)
                document = classified["document"]
                hit_group_class = HitGroupClass(
                        group_id=document.group_id,
                        classes=most_likely,
                        probabilities=classified["probabilities"])
                hit_group_class.save()
        except IOError:
            # We do not want make hit group details page unavailable when
            # classifier file does not exist.
            pass

    if hit_group_class is not None:
        hit_group_class_label = NaiveBayesClassifier.label(
                hit_group_class.classes
            )
    else:
        hit_group_class_label = NaiveBayesClassifier.label()

    params = {
        'multichart': False,
        'columns': HIT_DETAILS_COLUMNS,
        'title': '#Hits',
        'class': hit_group_class_label,
    }

    def hit_group_details_data_formater(input):
        for cc in input:
            yield {
                'date': cc['start_time'],
                'row': (str(cc['hits_available']),),
            }

    dicts = query_to_dicts(
                """ select start_time, hits_available from hits_mv
                    where group_id = '{}' order by start_time asc """
                .format(hit_group_id))
    data = hit_group_details_data_formater(dicts)
    params['date_from'] = hit_group.occurrence_date
    params['date_to'] = datetime.datetime.utcnow()
    params['data'] = data
    params['hit_group'] = hit_group
    return direct_to_template(request, 'main/hit_group_details.html', params)


@never_cache
def classification(request, classes=None):
    """ Displays charts with variability of classes in time. """
    all_classes = sorted(LABELS.keys())
    max_classes = sum(all_classes)
    classes = int(classes) if classes is not None else 0
    if classes > max_classes:
        raise Http404 
    top_tabs = map(lambda c: ClassificationTab(classes, c), all_classes)
    if classes > 0:
        chosen_classes = []
        for cls in all_classes:
            if classes & cls:
                chosen_classes.append(cls)
    else:
        chosen_classes = [0]
        num_classes = 1
    num_classes = len(chosen_classes)
    ctx = {
        "top_tabs": top_tabs,
        "multitabs": True,
        "multichart": False,
        "columns": (("date", "Date"),) +
                   # Create a column description for a quantity of each class.
                   tuple(map(lambda c: ("number", str(c)), chosen_classes)),
        "title": "Classification",
        "active_tabs": chosen_classes,
    }

    def _data_formatter(input):
        for cc in input:
            yield {
                "date": cc[0],
                "row": (str(cc[l + 1]) for l in range(num_classes)),
            }

    date_from, date_to = get_time_interval(request.GET, ctx, days_ago=7)
    if classes > 0:
        # Create a list of columns corresponding to the available classes.
        # This is a pivot query. For example it translates record from:
        # crawl_id | classess | hits_available
        # 735      | 0        | 12
        # 735      | 1        | 18
        # 735      | 2        | 98
        # 736      | 0        | 7
        # 736      | 1        | 17
        # 736      | 2        | 99
        # to the form that is easy to use in templates:
        # crawl_id | 0  | 1  | 2
        # 735      | 12 | 18 | 98
        # 736      | 7  |17  | 99
        # Given from http://sykosomatic.org/2011/09/pivot-tables-in-postgresql/
        columns = map(lambda l: "COALESCE(MAX(CASE classes "
                                    "WHEN {0} THEN hits_available END"
                                "), 0) AS \"{0}\"".format(l), chosen_classes)
        query_prefix = \
        """
            SELECT start_time, {}
            FROM main_hitgroupclassaggregate
        """.format(", ".join(columns))
    else:
        query_prefix = \
        """
            SELECT start_time, sum(hits_available) AS "0"
            FROM main_hitgroupclassaggregate
        """ 
    query = \
    """ {}
        WHERE start_time >= \'{}\' AND start_time <= \'{}\'
        GROUP BY crawl_id, start_time
        ORDER BY start_time ASC
    """.format(query_prefix, date_from, date_to)
    data = query_to_lists(query)

    def _anomalies(row, others):
        lgt = len(others)
        siz = len(row)
        mids = [sum(map(lambda o: o[i], others)) / lgt for i in range(1, siz)]
        abss = [abs(mids[i - 1] - row[i]) for i in range(1, siz)]
        return [i for i in range(1, siz) if abss[i - 1] > 7000]

    def _fixer(row, others, anomalies):
        lgt = len(others)
        for a in anomalies:
            val = sum(map(lambda o: o[a], others)) / lgt
            row[a] = val
        return row

    if settings.DATASMOOTHING:
        data = plot.vrepair(list(data), _anomalies, _fixer, 8)
    else:
        data = list(data)
    ctx['data'] = _data_formatter(data)
    return direct_to_template(request, 'main/graphs/timeline.html', ctx)


@never_cache
def classification_report(request, classes):
    ctx = {}
    date_from, date_to = get_time_interval(request.REQUEST, ctx, days_ago=1)
    page = int(request.REQUEST.get("page", 1))
    size = int(request.REQUEST.get("size", 5))
    query = \
    """ SELECT hmv.crawl_id, hmv.start_time, hgcls.classes, 
               hgcnt.group_id, hgcnt.title, hgcnt.description
        FROM hits_mv AS hmv
        JOIN main_hitgroupclass AS hgcls ON hmv.group_id = hgcls.group_id
        JOIN main_hitgroupcontent AS hgcnt ON hgcls.group_id = hgcnt.group_id
        WHERE hmv.start_time >= '{}' AND hmv.start_time < '{}' AND 
              hgcls.classes & {} <> 0
        ORDER BY start_time ASC
        LIMIT {}
        OFFSET {}
    """.format(date_from, date_to, classes, size, (page - 1) * size)
    data = query_to_dicts(query)
    def _data_formatter(input):
        for cc in input:
            yield cc[0], cc[1], cc[2]
    # data = _data_formatter(data)
    ctx["data"] = data
    ctx["classes"] = classes
    ctx["first_page"] = page == 1
    ctx["last_page"] = False # TODO finish it.
    ctx["next_page"] = page + 1
    ctx["prev_page"] = page - 1
    if size != 5:
        ctx["size"] = size
    return direct_to_template(request, 'main/classification_report.html', ctx)


def search(request):
    params = {}
    if request.method == 'POST' and 'query' in request.POST:
        params['query'] = request.POST['query']
    return direct_to_template(request, 'main/search.html', params)


class HitGroupContentSearchView(SearchView):

    def build_page(self):
        form = self.form
        if form is not None:
            self.results_per_page = form.hits_per_page_or_default()
        return super(HitGroupContentSearchView, self).build_page()

    def extra_context(self):
        context = super(HitGroupContentSearchView, self).extra_context()
        submit_url = ""
        form = self.form
        if form is not None:
            submit_url = form.submit_url()
        results = self.results
        if results is None:
            results = []
        context.update({"submit_url": submit_url})
        context.update({"total_count": results.count()})
        return context


@never_cache
def haystack_search(request):
    search_view = HitGroupContentSearchView(
            form_class=HitGroupContentSearchForm,
            template="main/search.html")
    return search_view(request)


class GeneralTabEnum:
    """Describes available tabs on the general view."""

    __metaclass__ = EnumMetaclass

    ALL = 0
    HITS = 1
    REWARDS = 2
    PROJECTS = 3
    SPAM = 4

    ENUM_FIELDS = EnumMetaclass.ENUM_FIELDS + ['urls']
    EXTRA_FIELDS = {
        'urls': lambda d: dict([
            (v, reverse('graphs_general', kwargs={'tab_slug': slug}))
            for v, slug in d['slugs'].items()])
    }

    display_names = {
        ALL: 'General data',
        HITS: 'HITs'
    }

    data_set_processor = {
        ALL: lambda x: x,
        HITS: lambda x: general_tab_data_formatter(0, x),
        REWARDS: lambda x: general_tab_data_formatter(1, x),
        PROJECTS: lambda x: general_tab_data_formatter(2, x),
        SPAM: lambda x: general_tab_data_formatter(3, x),
    }

    graph_columns = OrderedDict([
        ('date', ('date', 'Date')),
        (HITS, ('number', '#HITs')),
        (REWARDS, ('number', 'Rewards($)')),
        (PROJECTS, ('number', '#Projects')),
        (SPAM, ('number', '#Spam Projects')),
    ])

    @classmethod
    def get_graph_columns(cls, tab):
        if tab == cls.ALL:
            return tuple(cls.graph_columns.values())
        return (cls.graph_columns['date'], cls.graph_columns[tab])

    @classmethod
    def get_tab_title(cls, tab):
        return cls.display_names[tab]


class ArrivalsTabEnum:
    """Describes available tabs on the general view."""

    __metaclass__ = EnumMetaclass

    ALL = 0
    ARRIVALS = 1
    COMPLETED = 2

    ENUM_FIELDS = EnumMetaclass.ENUM_FIELDS + ['urls']
    EXTRA_FIELDS = {
        'urls': lambda d: dict([
            (v, reverse('graphs_arrivals', kwargs={'tab_slug': slug}))
            for v, slug in d['slugs'].items()])
    }

    display_names = {
        ALL: 'Arrivals + Completitions'
    }

    data_set_processor = {
        ALL: lambda x: model_fields_formatter(
            ['arrivals', 'arrivals_value', 'processed', 'processed_value'], x),
        ARRIVALS: lambda x: model_fields_formatter(
            ['arrivals', 'arrivals_value'], x),
        COMPLETED: lambda x: model_fields_formatter(
            ['processed', 'processed_value'], x),
    }

    graph_columns = OrderedDict([
        ('date', [('date', 'Date')]),
        (ARRIVALS, [('number', '#HIT arrived'),
                    ('number', 'Reward arrived($)')]),
        (COMPLETED, [('number', '#HIT completed'),
                     ('number', 'Reward completed($)')]),
    ])

    @classmethod
    def get_tab_title(cls, tab):
        return cls.display_names[tab]

    @classmethod
    def get_graph_columns(cls, tab):
        if tab == cls.ALL:
            return tuple(chain(*cls.graph_columns.values()))
        return tuple(chain(cls.graph_columns['date'] + cls.graph_columns[tab]))


class ClassificationTab:
    """ Describes avalable tabs on the classification view. 
        This is only a stube. """

    def __init__(self, classes, value):
        self.switch = value
        self.value = classes - value if classes & value else classes + value
        self.url = reverse("classification", args=(self.value, ))
        self.display_name = LABELS[value]
