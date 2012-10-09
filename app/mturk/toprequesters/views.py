# -*- coding: utf-8 -*-

from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic.simple import direct_to_template
from django.views.decorators.cache import never_cache

from mturk.toprequesters.reports import ToprequestersReport


@never_cache
def top_requesters(request, tab=None):
    """Crud handles the table rendering."""
    try:
        tab = int(tab)
    except Exception:
        pass
    if tab not in ToprequestersReport.values:
        messages.warning(request, 'Unknown report type: {0}'.format(tab))
        return redirect('graphs_top_requesters',
                        tab=ToprequestersReport.values[0])
    ctx = {
        'title': 'Top-1000 Recent Requesters',
        'tab_enum': ToprequestersReport.display_names,
        'active_tab': tab,
        'report_meta': ToprequestersReport.get_report_meta(tab),
    }
    return direct_to_template(request, 'toprequesters/crud.html', ctx)
