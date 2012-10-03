from tastypie import fields, resources

from mturk.main.models import HitGroupContent, HitGroupStatus


class HitGroupContentResource(resources.ModelResource):
    """Main api resource for accessing HitGroupContent."""

    has_hashed_group_id = fields.BooleanField(attribute='group_id_hashed')
    date_posted = fields.DateTimeField(attribute='occurrence_date')

    class Meta:
        queryset = HitGroupContent.objects.filter(is_public=True)
        allowed_methods = ['get', ]
        excludes = [
            'first_crawl', 'is_public', 'is_spam',
        ]
        filtering = {
            'id': resources.ALL,
            'group_id': resources.ALL,
            'has_hashed_group_id': resources.ALL,
            'requester_id': resources.ALL,
            'requester_name': resources.ALL,
            'reward': resources.ALL,
            'title': resources.ALL,
            'date_posted': resources.ALL,
            'time_alloted': resources.ALL,
        }
        ordering = [
            'id', 'title', 'group_id', 'requester_id', 'requester_name',
            'reward', 'date_posted', 'time_alloted', 'has_hashed_group_id'
        ]

    def dehydrate_keywords(self, bundle):
        return list(set(bundle.obj.keywords.split(", ")))

    def dehydrate_reward(self, bundle):
        return round(float(bundle.obj.reward), 2)


class HitGroupStatusResource(resources.ModelResource):
    """Main api resource for accessing HitGroupStatus."""

    crawl_date = fields.DateTimeField(attribute='crawl__start_time')
    hit_group_content_id = fields.IntegerField(attribute='hit_group_content__id')

    class Meta:
        queryset = HitGroupStatus.objects.filter(hit_group_content__is_public=True)
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
