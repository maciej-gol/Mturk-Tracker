from haystack import indexes
from haystack import site
from mturk.main.models import HitGroupContent


class HitGroupContentIndex(indexes.SearchIndex):

    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title') #" type="textTight" indexed="true" stored="true"/>
    description = indexes.CharField(model_attr='description') #" type="textTight" indexed="true" stored="true" required="false"/>
    group_id = indexes.CharField(model_attr='group_id') #type="string" indexed="true" stored="true"/>
    requester_id = indexes.CharField(model_attr='requester_id') #" type="string" indexed="true" stored="true"/>
    requester_name = indexes.CharField(model_attr='requester_name') #" type="textTight" indexed="true" stored="true"/>
    reward = indexes.DecimalField(model_attr='reward') #" type="double" indexed="true" stored="true"/>
#    content#" type="text_en" indexed="true" stored="true" required="false" compressed="true"/>
    keywords = indexes.CharField(model_attr='keywords') #" type="text_tags" indexed="true" stored="true" required="false" multiValued="true"/>
    qualifications = indexes.CharField(model_attr='qualifications') #" type="textTight" indexed="true" stored="true"/>
    occurrence_date = indexes.DateTimeField(model_attr='occurrence_date') #" type="date" indexed="true" stored="true"/>
    time_alloted = indexes.DecimalField(model_attr='time_alloted') #" type="int" indexed="true" stored="true"/>

    def index_queryset(self):
        return HitGroupContent.objects.all()

site.register(HitGroupContent, HitGroupContentIndex)
