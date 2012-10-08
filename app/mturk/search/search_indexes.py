from django.utils.html import strip_tags

from haystack import indexes
from haystack.query import SearchQuerySet
from haystack.models import SearchResult

from mturk.main.models import HitGroupContent
from mturk.classification.classifier import Labels


class HitGroupContentIndex(indexes.SearchIndex, indexes.Indexable):
    """Haystack search index for HitGroupContent objects.

    Most of this is rather straightforwards, however there is a number of
    custom/manual handling done behind the scenes:
    * imports are done using solr directly as haystack methods would run out of
    memory given the amount of data we have,
    * there is a custom handling of labels, which being bitmask fields in the
    datebase, require mapping into some solr-compatible structure (see below).

    Where are 'labels' ? (tldr; see HitGroupContentSearchResult below)

    There can be a number of label_* fields on the SearchResult object related
    to this resource. During solr import we are converting HitGroupContent
    classes into a variable number of fields having names:

      label_<label_enum_id>.

    If some document contains a label with id N, then the representing
    SearchResult (item of a haystack SearchQuerySet) obj will have:

      obj.label_N == N

    where N is an integer.

    """
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    description = indexes.CharField(model_attr='description')
    group_id = indexes.CharField(model_attr='group_id')
    requester_id = indexes.CharField(model_attr='requester_id')
    requester_name = indexes.CharField(model_attr='requester_name')
    reward = indexes.DecimalField(model_attr='reward')
    content = indexes.CharField(model_attr='html')
    keywords = indexes.MultiValueField(model_attr='keywords', faceted=True,
                                       null=True)
    qualifications = indexes.CharField(model_attr='qualifications', null=True)
    occurrence_date = indexes.DateTimeField(model_attr='occurrence_date')
    time_alloted = indexes.DecimalField(model_attr='time_alloted')

    # labels = (see the doc above)

    # Additional fields for sorting.
    title_sort = indexes.CharField()
    description_sort = indexes.CharField()
    requester_name_sort = indexes.CharField()

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


#
# Customizing behaviour for use with crud and to facilitate labels.
#
class HitGroupContentSearchResult(SearchResult):
    """SearchResult is the class of a single entry in a haystack SearchQuerySet.

    This class introduces handling for label_* fields adding two fields:
    * labels -- list of label_* field id's that are available on the instance,
    * get_labels_display -- list of labels display_names.

    """

    @property
    def labels(self):
        """Get list labels numerical representation."""
        labels = []
        for label in range(len(Labels.values)):
            try:
                label = getattr(self, 'label_{}'.format(label))
                label is not None and labels.append(label)
            except AttributeError:
                pass
        return labels

    def get_labels_display(self):
        """Get list of labels display names."""
        return [Labels.display_names[l] for l in self.labels]


class HitGroupContentSearchQuerySet(SearchQuerySet):
    """Extending the haystack's SearchQuerySet for use with solr and crud.

    This class adds:
    * related model property required by crud (used by tastypie)
    * labels as a single field using HitGroupContentSearchResource

    """

    model = HitGroupContent

    def __init__(self, *args, **kwargs):
        """The base __init__ makes sure the query and it's SearchResult are set.
        We need to replace it afterwards to introduce features of
        HitGroupContentSearchResult.

        """
        super(HitGroupContentSearchQuerySet, self).__init__(*args, **kwargs)
        self.query.set_result_class(HitGroupContentSearchResult)
