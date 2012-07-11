import string
from itertools import product

from django import forms
from haystack.forms import SearchForm


# Fields names.
TITLE_SORT = "title_sort"
DESCRIPTION_SORT = "description_sort"
REQUESTER_NAME_SORT = "requester_name_sort"
REWARD = "reward"
OCCURRENCE_DATE = "occurrence_date"
TIME_ALLOTED = "time_alloted"

TITLE = "title"
DESCRIPTION = "description"
REQUESTER_ID = "requester_id"
REQUESTER_NAME = "requester_name"
CONTENT = "content"
KEYWORDS = "keywords"
QUALIFICATIONS = "qualifications"

FIELDS = (TITLE, DESCRIPTION, CONTENT, REQUESTER_ID, REQUESTER_NAME, REWARD,
          OCCURRENCE_DATE, TIME_ALLOTED, KEYWORDS, QUALIFICATIONS,
          TITLE_SORT, DESCRIPTION_SORT, REQUESTER_NAME_SORT)

SEARCH_IN_FIELDS = (TITLE, DESCRIPTION, REQUESTER_ID, REQUESTER_NAME, CONTENT)

SORT_BY_FIELDS = (TITLE_SORT, DESCRIPTION_SORT, REQUESTER_NAME_SORT, REWARD,
                  OCCURRENCE_DATE, TIME_ALLOTED)

ORDERS = ("asc", "desc")
HITS_PER_PAGES = ("5", "10", "20", "50")

FIELDS_PRETTY = tuple(
        map(
            lambda s: " ".join(map(string.capitalize, s.split("_"))),
            FIELDS
        ))

FIELDS_PRETTY_DICT = dict(zip(FIELDS, FIELDS_PRETTY))
FIELDS_PRETTY_DICT[TITLE_SORT] = FIELDS_PRETTY_DICT[TITLE]
FIELDS_PRETTY_DICT[DESCRIPTION_SORT] = FIELDS_PRETTY_DICT[DESCRIPTION]
FIELDS_PRETTY_DICT[REQUESTER_NAME_SORT] = FIELDS_PRETTY_DICT[REQUESTER_NAME]

ORDERS_PRETTY = ("ascending", "descending")

SEARCH_IN_CHOICES = zip(
        SEARCH_IN_FIELDS,
        map(
            FIELDS_PRETTY_DICT.get,
            SEARCH_IN_FIELDS
        ))

SORT_BY_CHOICES = zip(
        map(
            lambda tupl: "{}_{}".format(tupl[0], tupl[1]),
            product(SORT_BY_FIELDS, ORDERS)
        ),
        map(
            lambda tupl: "{} ({})".format(FIELDS_PRETTY_DICT[tupl[0]], tupl[1]),
            product(SORT_BY_FIELDS, ORDERS_PRETTY)
        ))

HITS_PER_PAGE_CHOICES = zip(HITS_PER_PAGES, HITS_PER_PAGES)

DEFAULT_SEARCH_IN = SEARCH_IN_FIELDS # all fields
DEFAULT_SORT_BY = SORT_BY_CHOICES[0][0] # title_sort_asc
DEFAULT_HITS_PER_PAGE = HITS_PER_PAGES[0] # 5

class HitGroupContentSearchForm(SearchForm):
    search_in = forms.MultipleChoiceField(choices=SEARCH_IN_CHOICES,
                                          required=False)
    sort_by = forms.ChoiceField(choices=SORT_BY_CHOICES, required=False)
    hits_per_page = forms.ChoiceField(choices=HITS_PER_PAGE_CHOICES,
                                      required=False)

    def cleaned_data_or_empty(self):
        try:
            cleaned_data = self.cleaned_data
        except AttributeError:
            cleaned_data = { }
        return cleaned_data

    def search(self):
        """ Returns a search queryset. """
        search_queryset = super(HitGroupContentSearchForm, self).search()

        cleaned_data = self.cleaned_data_or_empty()
        query = cleaned_data.get("q", "")
        if not query:
            return search_queryset
        # Get fields for search in.
        search_in = cleaned_data.get("search_in", DEFAULT_SEARCH_IN)
        # Get field and order for sorting.
        sort_by = cleaned_data.get("sort_by", DEFAULT_SORT_BY).rsplit("_", 1)
        # Prepare for SearchQuerySet API.
        sort_by = "{}{}".format("" if sort_by[1] == "asc" else "-",
                                sort_by[0])
        kwargs = {}
        for field in search_in:
            kwargs[field] = query
        search_queryset = search_queryset.filter_and(**kwargs)
        search_queryset = search_queryset.order_by(sort_by)
        return search_queryset

    def submit_url(self):
        """ Builds an url for simple state holding between pages. """
        cleaned_data = self.cleaned_data_or_empty()
        query = cleaned_data.get("q", "")
        search_in = "".join(map(lambda f: "&search_in={}".format(f),
                            cleaned_data.get("search_in", [])))
        sort_by = "".join(map(lambda o: "&sort_by={}".format(o),
                          [cleaned_data.get("sort_by", DEFAULT_SORT_BY)]))
        hits_per_page = "".join(map(lambda hpp: "&hits_per_page={}".format(hpp),
                                [cleaned_data.get("hits_per_page", DEFAULT_HITS_PER_PAGE)]))
        return "?q={}{}{}{}".format(query, search_in, sort_by, hits_per_page)

    def hits_per_page_or_default(self):
        cleaned_data = self.cleaned_data_or_empty()
        try:
            hits_per_page = int(cleaned_data.get("hits_per_page",
                                                 DEFAULT_HITS_PER_PAGE))
        except ValueError:
            # If value is an empty string (or something else).
            hits_per_page = DEFAULT_HITS_PER_PAGE
        return hits_per_page
