from django.core.urlresolvers import reverse
from tenclouds.crud import fields
from tenclouds.crud import resources
from tenclouds.crud.qfilters import Group, ChoicesFilter, FullTextSearch
from mturk.main.forms import SEARCH_IN_CHOICES
from mturk.classification.classifier import Labels
from mturk.main.models import HitGroupContent


class HitGroupContentResource(resources.ModelResource):
    """Main api resource for accessing HitGroupContent."""

    id = fields.IntegerField(attribute="id")
    title = fields.CharField(attribute='title')
    description = fields.CharField(attribute='description')
    group_id = fields.CharField(attribute='group_id', title="Group ID")
    requester_id = fields.CharField(attribute='requester_id', title="Requester ID")
    requester_name = fields.CharField(attribute='requester_name', title="Requester name")
    reward = fields.DecimalField(attribute='reward')
    content = fields.CharField(attribute='html')
    keywords = fields.CharField(attribute='keywords')
    qualifications = fields.CharField(attribute='qualifications')
    date_posted = fields.DateTimeField(attribute='occurrence_date', title="Date posted")
    time_allotted = fields.DecimalField(attribute='time_alloted', title="Time allotted")
    classes = fields.IntegerField(attribute="classes", null=True)

    class Meta:
        list_allowed_methods = ['get', ]
        queryset = HitGroupContent.objects.all()
        per_page = [10, 20, 50]
        ordering = [
            'id', 'date_posted', 'title', 'requester_name', 'reward',
            'time_allotted',
        ]
        default_ordering = ['-date_posted']

    def dehydrate_keywords(self, bundle):
        return list(set(bundle.obj.keywords.split(", ")))

    def dehydrate_reward(self, bundle):
        return round(bundle.obj.reward, 2)


class HitGroupContentSearchResource(HitGroupContentResource):
    """Api resource for accessing HitGroupContent results stored in the search
    index.

    # TODOS:
    # 1) upgrade to haystack 2.0 for SQ support
    # 2) refactor dj-crud to allow specifying queryset object
    # 3) change objects to haystack searchqueryset

    """

    # id stores the document id of a file in the index
    index_id = fields.IntegerField(attribute="id")
    # pk stores the database id
    id = fields.IntegerField(attribute="pk")

    # url fields
    group_url = fields.CharField()
    requester_url = fields.CharField()

    class Meta(HitGroupContentResource.Meta):
        queryset = HitGroupContent.objects.all()
        fields = [
            'id', 'index_id', 'group_id', 'date_posted',
            'title', 'requester_name', 'requester_id',
            'time_allotted', 'keywords', 'reward', 'description',
            'group_url', 'requester_url',
        ]
        filters = (
            Group('Search in', ChoicesFilter(SEARCH_IN_CHOICES, 'search'),
                join='or'),
            Group('Labels', ChoicesFilter(
                Labels.display_choices, 'labels'), join='or'),
            Group('Keywords', FullTextSearch('title', 'title__icontains'))
        )

    def dehydrate_group_url(self, bundle):
        return reverse('hit_group_details',
            kwargs={'hit_group_id': bundle.obj.group_id})

    def dehydrate_requester_url(self, bundle):
        return reverse('requester_details',
            kwargs={'requester_id': bundle.obj.requester_id})
