from django.db.models import Q

from tenclouds.crud.qfilters import ChoicesFilter, Filter, Group


class MultiFieldChoiceFilter(ChoicesFilter):
    """Allows filtering over a number of fields on an object that have a similar
    name pattern.

    Keyword arguments:
    choices -- (key, display_name) pairs as in ChoicesFilter
    filter_attr -- name of the filter on the SomeResource
    field_template -- template to format with choice key used for querying

    Why do this? Example:

    Imagine there is a database index with label_* fields. They don't have to
    be mapped at all to then index, just be there, but let's say it looks like:

    class SomeIndex(indexes.SearchIndex, indexes.Indexable)
        label_0 = indexes.IntegerField(..)
        label_1 = indexes.IntegerField(..)
        label_2 = indexes.IntegerField(..)

    Then, filtering over labels can can be defined the following way:

    class SomeResource(resources.ModelResource):
        ...
        class Meta:
            filters = (
                Group('Labels',
                    MultiFieldChoiceFilter(
                        Labels.display_choices,
                        'labels', 'label_{}__exact'
                    ),
                    join='or'
                ),
            )

    """

    def __init__(self, choices, filter_attr, field_template):
        self.choices = choices
        self.filter_attr = filter_attr
        self.field_template = field_template

    def filter_fields(self, request):
        for choice, choice_name in self.choices:
            query = Q(**{self.field_template.format(choice): unicode(choice)})
            field = {self.filter_attr: choice}
            yield Filter(choice_name, query=query, **field)


class InactiveFilterGroup(Group):
    """Group that will perform no queries regardless of Fields passed.

    Used to have the filteres rendered and included in the requests, but
    suppressing their normal behaviour to perform the queries elsewhere.

    """
    def apply_filters(self, request, query, filter_keys):
        return query


class FulltextSearchGroup(Group):
    """Filter group designed to contain a single FullTextSearch control to use
    for searching, that can be made aware of some other Filter containing names
    of the fields to search in.

    Currently, any filter contained by this group will have it's ``filters``
    property changed to reflect the selected search_in parameters (the selected
    or all if no selection is specified).

    """
    filter_query = '{}__icontains'
    """Query to use when searching in fields."""

    def __init__(self, name, *fields, **kwargs):
        self.name = name
        self.fields = fields
        # I don't think 'and' joiner will be of any use here, nor will it work
        # without extra work on the filter (FullTextSearch filter implies an OR
        # query by default.
        assert kwargs.get('join') is not 'and', 'And joiner is not implemented!'
        self.query_joiner = 'or'
        #self.query_joiner = kwargs.get('join', 'and')

        self.search_in_field = kwargs.get('search_in_field')
        self.search_in_values = kwargs.get('search_in_values')
        assert self.search_in_field, 'Please specify search_in kwargs.'
        assert self.search_in_values, 'Please specify a search_in_values kwarg.'

        if self.query_joiner not in ['and', 'or']:
            raise TypeError('Unknown query joiner: %s' % self.query_joiner)

    def __add_search_in_to_filters(self, filter_keys, filters):
        """Alters filter's default ``filters`` property."""
        # get search in field names
        search_in = [f.split(':') for f in filter_keys if ':' in f]
        search_in = [f[1] for f in search_in
            if f[0] == self.search_in_field and len(f) > 1]

        # apply search is all search_in_values if none is specified
        if not search_in:
            search_in = self.search_in_values

        # add search_in to filter's inner filters
        for fk in filters:
            fk[0].filters = [self.filter_query.format(si) for si in search_in]

        return filters

    def apply_filters(self, request, query, filter_keys):
        """This only differs from the original by __add_search_in_to_filters
        call.

        """
        filters = ((self.filter_by_key(key, request), key)
                   for key in filter_keys)
        filters = [(f, k) for f, k in filters if f]

        if not filters:
            return query

        # handle search_in
        self.__add_search_in_to_filters(filter_keys, filters)

        # filter using AND
        if self.query_joiner == 'and':
            for f, key in filters:
                query = query.filter(f.build_filters(key))
            return query

        # filter using OR
        elif self.query_joiner == 'or':
            q = None
            for f, key in filters:
                if q is None:
                    q = f.build_filters(key)
                else:
                    q |= f.build_filters(key)
            if q:
                query = query.filter(q)
            return query

        raise TypeError('Unknown query joiner: %s' % self.query_joiner)
