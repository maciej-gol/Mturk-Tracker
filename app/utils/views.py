import time
from datetime import date, datetime, timedelta


def get_time_interval(get, ctx, encode=True, days_ago=30):
    """ Shortcut function that returns a time interval from the ``get``
        dictionary, and stores it in the ``ctx`` dictionary.
        The ``days_ago`` is a number of days from now, in case
        when the ``get`` does not contain any information. """
    if 'date_from' in get:
        date_from = date_from_str(get['date_from'])
    else:
        date_from = (date.today() - timedelta(days=days_ago))
    if 'date_to' in get:
        date_to = date_from_str(get['date_to'])
    else:
        date_to = (date.today() + timedelta(days=1))
    if encode:
        date_from_enc = date_from.strftime('%m/%d/%Y')
        date_to_enc = date_to.strftime('%m/%d/%Y')
    else:
        date_from_enc = date_from
        date_to_enc = date_to
    ctx['date_from'] = date_from_enc
    ctx['date_to'] = date_to_enc
    return date_from, date_to


def date_from_str(s):
    return datetime(*time.strptime(s, '%m/%d/%Y')[:6])
