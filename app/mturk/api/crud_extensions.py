from django.db.models import Q
from tenclouds.crud.qfilters import ChoicesFilter, Filter
# from django.models import Q


class MultiFieldChoiceFilter(ChoicesFilter):
    """Allows filtering over a number of fields on an object that have a similar
    name pattern.

    Keyword arguments:
    choices -- (key, display_name) pairs as in ChoicesFilter
    filter_attr -- name of the filter on the SomeResource
    field_template -- template to format with choice key used for querying
    choice -- value to get

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
                        'labels', 'label_{}__iexact', choice=1
                    ),
                    join='or'
                ),
            )

    """

    def __init__(self, choices, filter_attr, field_template, choice):
        self.choices = choices
        self.filter_attr = filter_attr
        self.choice = choice
        self.field_template = field_template

    def filter_fields(self, request):
        for query_value, name in self.choices:
            query = Q(**{self.field_template.format(query_value): self.choice})
            field = {self.filter_attr: query_value}
            yield Filter(name, query=query, **field)
