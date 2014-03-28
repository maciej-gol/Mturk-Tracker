from django.core.urlresolvers import reverse

from tenclouds.crud import fields
# from tenclouds.crud import resources
from tenclouds.crud.qfilters import Group, ChoicesFilter, FullTextSearch

from mturk.classification.classifier import Labels

from crud_extensions import (MultiFieldChoiceFilter, InactiveFilterGroup,
    FulltextSearchGroup, SearchResource)
from search_indexes import HitGroupContentSearchQuerySet
from enums import SearchInEnum


class HitGroupContentSearchResource(SearchResource):
    """Api resource for accessing HitGroupContent results stored in the search
    index.

    """
    # pk stores the database id
    id = fields.IntegerField(attribute="pk", null=True)
    # id stores the document id of a file in the index
    index_id = fields.CharField(attribute="id", null=True)
    title = fields.CharField(attribute='title', null=True)
    description = fields.CharField(attribute='description', null=True)
    group_id = fields.CharField(attribute='group_id', title="Group ID", null=True)
    requester_id = fields.CharField(attribute='requester_id', title="Requester ID", null=True)
    requester_name = fields.CharField(attribute='requester_name', title="Requester name", null=True)
    reward = fields.DecimalField(attribute='reward', null=True)
    content = fields.CharField(attribute='html', null=True)
    keywords = fields.CharField(attribute='keywords', null=True)
    qualifications = fields.CharField(attribute='qualifications', null=True)
    date_posted = fields.DateTimeField(attribute='occurrence_date', title="Date posted", null=True)
    time_allotted = fields.DecimalField(attribute='time_alloted', title="Time allotted", null=True)
    labels = fields.ListField(attribute="labels", null=True)

    # url fields
    group_url = fields.CharField()
    requester_url = fields.CharField()

    # dedicated fields for haystack to search on
    title_sort = fields.CharField(attribute='title_sort', null=True)
    description_sort = fields.CharField(attribute='description_sort', null=True)
    requester_name_sort = fields.CharField(attribute='requester_name_sort', null=True)

    class Meta:
        queryset = HitGroupContentSearchQuerySet()
        allowed_methods = ['get', ]
        per_page = [10, 20, 50]
        fields = [
            'id', 'index_id', 'group_id', 'date_posted',
            'title', 'requester_name', 'requester_id',
            'time_allotted', 'keywords', 'reward', 'description',
            'group_url', 'requester_url', 'labels'
        ]
        ordering = [
            'date_posted', 'title', 'requester_name', 'reward',
            'time_allotted', 'description',
            'title_sort', 'description_sort', 'requester_name_sort',
        ]
        search_ordering_fields_map = {
            'title': 'title_sort',
            'requester_name': 'requester_name_sort',
            'description': 'description_sort',
        }
        default_ordering = ['-date_posted']

        # when editing the filters below, make sure to check if the widget
        # assignment in js/search/crudstart.coffee shouldn't be changed too
        filters = (
            FulltextSearchGroup('Search', FullTextSearch('search'),
                search_in_field='search_in',
                search_in_values=SearchInEnum.values),
            InactiveFilterGroup('Search in fields',
                ChoicesFilter(SearchInEnum.display_choices, 'search_in'),
            ),
            Group('Hit categories', MultiFieldChoiceFilter(
                Labels.display_choices, 'labels', 'label_{}__exact'),
                join='or'
            ),
        )

    def dehydrate_keywords(self, bundle):
        return list(set(bundle.obj.keywords[0].split(", ")))

    def dehydrate_group_url(self, bundle):
        return reverse('hit_group_details',
            kwargs={'hit_group_id': bundle.obj.group_id})

    def dehydrate_requester_url(self, bundle):
        return reverse('requester_details',
            kwargs={'requester_id': bundle.obj.requester_id})

    def dehydrate_reward(self, bundle):
        return round(float(bundle.obj.reward), 2)

    def dehydrate_labels(self, bundle):
        return bundle.obj.get_labels_display()


class HitSearchResource(HitGroupContentSearchResource):
    class Meta(HitGroupContentSearchResource.Meta):
        per_page = [6, 12, 24, 36]

        filters = (
            Group('Query', FullTextSearch('query',
                                          'title', 'description', 'content',
                                          'keywords', 'qualifications')
                  ),
            Group('Requester', FullTextSearch('requester', 'requester_id'),
                  join='or'),
        )
