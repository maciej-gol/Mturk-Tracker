from tastypie import fields, resources

from mturk.main.models import HitGroupContent, HitGroupStatus


class HitGroupContentResource(resources.ModelResource):
    """Main api resource for accessing HitGroupContent."""

    id = fields.IntegerField(attribute="id")
    title = fields.CharField(attribute='title')
    description = fields.CharField(attribute='description')
    group_id = fields.CharField(attribute='group_id')
    requester_id = fields.CharField(attribute='requester_id')
    requester_name = fields.CharField(attribute='requester_name')
    reward = fields.DecimalField(attribute='reward')
    content = fields.CharField(attribute='html')
    keywords = fields.CharField(attribute='keywords')
    qualifications = fields.CharField(attribute='qualifications')
    date_posted = fields.DateTimeField(attribute='occurrence_date')
    time_allotted = fields.DecimalField(attribute='time_alloted')

    # TODO: add labels handling
    # labels = fields.IntegerField(attribute="classes", null=True)

    class Meta:
        queryset = HitGroupContent.objects.all()
        allowed_methods = ['get', ]

    def dehydrate_keywords(self, bundle):
        return list(set(bundle.obj.keywords.split(", ")))

    def dehydrate_reward(self, bundle):
        return round(float(bundle.obj.reward), 2)


class HitGroupStatusResource(resources.ModelResource):
    """Main api resource for accessing HitGroupStatus."""

    crawl_date = fields.DateTimeField(attribute='crawl__start_time')
    hit_group_content_id = fields.IntegerField(attribute='hit_group_content__id')

    class Meta:
        queryset = HitGroupStatus.objects.all()
        allowed_methods = ['get', ]
        fields = ['id', 'group_id', 'hits_available', 'hit_expiration_date']
        filtering = {
            'id': resources.ALL,
            'crawl_date': resources.ALL,
            'hits_available': resources.ALL,
            'hit_expiration_date': resources.ALL,
            'hit_group_content_id': resources.ALL,
            'group_id': resources.ALL,
        }
        ordering = [
            'id', 'crawl_date', 'hits_available', 'hit_expiration_date',
            'hit_group_content_id'
        ]
