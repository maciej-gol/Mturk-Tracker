from django.utils.html import strip_tags

from haystack import indexes
from haystack import site
from mturk.main.models import HitGroupContent


class HitGroupContentIndex(indexes.SearchIndex):

    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    description = indexes.CharField(model_attr='description')
    group_id = indexes.CharField(model_attr='group_id')
    requester_id = indexes.CharField(model_attr='requester_id')
    requester_name = indexes.CharField(model_attr='requester_name')
    reward = indexes.DecimalField(model_attr='reward')
    content = indexes.CharField(model_attr='html')
    keywords = indexes.MultiValueField(model_attr='keywords')
    qualifications = indexes.CharField(model_attr='qualifications')
    occurrence_date = indexes.DateTimeField(model_attr='occurrence_date')
    time_alloted = indexes.DecimalField(model_attr='time_alloted')

    def prepare_description(self, obj):
        return strip_tags(obj.description)

    def prepare_content(self, obj):
        return strip_tags(obj.html)

    def prepare_keywords(self, obj):
        return obj.keywords.split(',')

    def index_queryset(self):
        return HitGroupContent.objects.all()


site.register(HitGroupContent, HitGroupContentIndex)
