from tenclouds.crud import fields
from tenclouds.crud import resources

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
        queryset = HitGroupContent.objects.all()
        list_allowed_methods = ['get', ]
        per_page = [10, 20, 50]
        ordering = [
            'id', 'date_posted', 'title', 'requester_name', 'reward',
            'time_allotted',
        ]
        default_ordering = ['-date_posted']

    def dehydrate_keywords(self, bundle):
        return list(set(bundle.obj.keywords.split(", ")))

    def dehydrate_reward(self, bundle):
        return round(float(bundle.obj.reward), 2)
