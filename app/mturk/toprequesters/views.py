# -*- coding: utf-8 -*-

from django.core.urlresolvers import reverse
from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic.simple import direct_to_template
from django.views.decorators.cache import never_cache

from mturk.toprequesters.reports import ToprequestersReport

# TODO: once doing an admin revamp, make sure to move the admin to this module
from mturk.main import admin


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

        return direct_to_template(request, 'toprequesters/main.html', ctx)

    return _top_requesters(request)
