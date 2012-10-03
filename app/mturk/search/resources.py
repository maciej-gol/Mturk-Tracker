from django.core.urlresolvers import reverse

from tenclouds.crud import fields
from tenclouds.crud import resources
from tenclouds.crud.qfilters import Group, ChoicesFilter, FullTextSearch

from mturk.classification.classifier import Labels

from crud_extensions import MultiFieldChoiceFilter
from search_indexes import HitGroupContentSearchQuerySet
from enums import SearchInEnum


class HitGroupContentSearchResource(resources.ModelResource):
    """Api resource for accessing HitGroupContent results stored in the search
    index.

    """
    # pk stores the database id
    id = fields.IntegerField(attribute="pk")
    # id stores the document id of a file in the index
    index_id = fields.CharField(attribute="id")
    title = fields.CharField(attribute='title')
    description = fields.CharField(attribute='description')
    group_id = fields.CharField(attribute='group_id', title="Group ID")
    requester_id = fields.CharField(attribute='requester_id', title="Requester ID")
    requester_name = fields.CharField(attribute='requester_name', title="Requester name")
    reward = fields.DecimalField(attribute='reward')
    content = fields.CharField(attribute='html', null=True)
    keywords = fields.CharField(attribute='keywords')
    qualifications = fields.CharField(attribute='qualifications')
    date_posted = fields.DateTimeField(attribute='occurrence_date', title="Date posted")
    time_allotted = fields.DecimalField(attribute='time_alloted', title="Time allotted")
    labels = fields.ListField(attribute="labels", null=True)

    # url fields
    group_url = fields.CharField()
    requester_url = fields.CharField()

    class Meta:
        queryset = HitGroupContentSearchQuerySet()
        list_allowed_methods = ['get', ]
        per_page = [10, 20, 50]
        fields = [
            'id', 'index_id', 'group_id', 'date_posted',
            'title', 'requester_name', 'requester_id',
            'time_allotted', 'keywords', 'reward', 'description',
            'group_url', 'requester_url', 'labels'
        ]
        ordering = [
            'id', 'date_posted', 'title', 'requester_name', 'reward',
            'time_allotted',
        ]
        default_ordering = ['-date_posted']
        filters = (
            Group('Labels', MultiFieldChoiceFilter(
                Labels.display_choices, 'labels', 'label_{}__exact'),
                join='or'
            ),
            Group('Search in',
                ChoicesFilter(SearchInEnum.display_choices, 'search'),
                join='or'
            ),
            Group('Keywords', FullTextSearch('title', 'title__icontains')),
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
