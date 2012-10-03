from django.db.models import Q

from tenclouds.crud.qfilters import ChoicesFilter, Filter


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
