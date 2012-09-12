from django.utils.html import strip_tags
from tenclouds.crud import fields
from tenclouds.crud import resources

from mturk.main.models import HitGroupContent


class HitGroupContentResource(resources.ModelResource):

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
    occurrence_date = fields.DateTimeField(attribute='occurrence_date')
    time_alloted = fields.DecimalField(attribute='time_alloted')
    classes = fields.IntegerField(attribute="classes", null=True)

    class Meta:
        list_allowed_methods = ['get', ]
        queryset = HitGroupContent.objects.all()
        per_page = 10
        ordering = ['occurrence_date', 'title']
        #fields = ['id', 'title', 'is_available', 'author_name']
