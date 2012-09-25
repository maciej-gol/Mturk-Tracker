from django.utils.html import strip_tags

from haystack import indexes
from mturk.main.models import HitGroupContent


class HitGroupContentIndex(indexes.SearchIndex, indexes.Indexable):

    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    description = indexes.CharField(model_attr='description')
    group_id = indexes.CharField(model_attr='group_id')
    requester_id = indexes.CharField(model_attr='requester_id')
    requester_name = indexes.CharField(model_attr='requester_name')
    reward = indexes.DecimalField(model_attr='reward')
    content = indexes.CharField(model_attr='html')
    keywords = indexes.MultiValueField(model_attr='keywords', faceted=True, null=True)
    qualifications = indexes.CharField(model_attr='qualifications', null=True)
    occurrence_date = indexes.DateTimeField(model_attr='occurrence_date')
    time_alloted = indexes.DecimalField(model_attr='time_alloted')

    # Additional fields for sorting.
    title_sort = indexes.CharField()
    description_sort = indexes.CharField()
    requester_name = indexes.CharField()

    def prepare_description(self, obj):
        return strip_tags(obj.description)

    def prepare_content(self, obj):
        return strip_tags(obj.html)

    def prepare_keywords(self, obj):
        return obj.keywords.split(',')

    def get_model(self):
        return HitGroupContent

    def index_queryset(self):
        return self.get_model().objects.all()
