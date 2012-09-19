from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import Http404
from django.views.generic.simple import direct_to_template
from django.views.decorators.cache import never_cache

from mturk.classification import LABELS
from mturk.main import plot
from utils.views import get_time_interval
from utils.sql import query_to_dicts, query_to_lists


@never_cache
def aggregates(request, classes=None):
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
def report(request, classes):
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


class ClassificationTab:
    """ Describes avalable tabs on the classification view. 
        This is only a stube. """

    def __init__(self, classes, value):
        self.switch = value
        self.value = classes - value if classes & value else classes + value
        self.url = reverse("classification_aggregates", args=(self.value, ))
        self.display_name = LABELS[value]
