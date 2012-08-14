# -*- coding: utf-8 -*-

from django.template.defaultfilters import slugify


class EnumMetaclass(type):
    """Metaclass for enumerations.

    You must define the values using UPPERCASE names as long or int.

    Generates:
    cls.names -- reverse dictionary mapping value to name
    cls.choices -- sorted list of (id, name) pairs suitable for model choices
    cls.values -- list of values defined by the enumeration
    cls.trans_name -- reverse dictionary mapping value to string ready for
    translation
    cls.display_names -- cls.names items processed for display
    cls.slugs -- slugified versions of display_names
    cls.value_for_slug -- reverse mapping for the above
    cls.enum_dict -- dictionary containing all details for the value, this is:
    slug, name, display_name, trans_name and value,

    Example:
    class X(object):
        __metaclass__ = EnumMetaclass
        A = 1
        B = 2
        C = 3
        LONG_NAME = 4

    >>> X.names
    {1: 'A', 2: 'B', 3: 'C', 4: 'LONG_NAME'}

    >>> X.values
    [1, 2, 3, 4]

    >>> X.choices
    [(1, 'A'), (2, 'B'), (3, 'C'), (4, 'LONG_NAME')]

    >>> X.trans_names
    {1: 'X.A', 2: 'X.B', 3: 'X.C', 4: 'X.LONG_NAME'}

    >>> X.diplay_names
    {1: 'A', 2: 'B', 3: 'C', 4: 'Long name'}

    >>> X.slugs
    {1: 'a', 2: 'b', 3: 'c', 4: 'long-name'}

    >>> X.value_for_slug
    {'a': 1, 'b': 2, 'c': 3, 'long-name': 4}

    """
    def __new__(cls, name, bases, d):
        names = dict()
        pairs = []
        values = []
        trans_names = dict()
        for x in d:
            if x.isupper() and (isinstance(d[x], int) or isinstance(d[x], long)):
                names[d[x]] = x
                pairs.append((d[x], x))
                values.append(d[x])
                trans_names[d[x]] = name + u"." + x
        pairs.sort()
        d['names'] = names
        d['choices'] = pairs
        d['values'] = values
        d['trans_names'] = trans_names

        # create display names
        dn = lambda x: (x[0].title() + x[1:].lower()).replace('_', ' ')
        display_names = dict([(n[0], dn(n[1])) for n in d['names'].items()])
        # update with existing ones
        display_names.update(d.get('display_names', {}))
        d['display_names'] = display_names
        d['slugs'] = dict([(n[0], slugify(n[1]))
            for n in d['display_names'].items()])
        d['value_for_slug'] = dict([(n[1], n[0]) for n in d['slugs'].items()])

        d['enum_dict'] = dict([(v, {'value': v}) for v in values])
        for v in d['enum_dict']:
            for l in ['slugs', 'names', 'display_names', 'trans_names']:
                d['enum_dict'][v][l[:-1]] = d[l][v]

        return type.__new__(cls, name, bases, d)
