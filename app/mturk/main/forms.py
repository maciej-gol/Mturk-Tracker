import string
from itertools import product

from django import forms
from haystack.forms import SearchForm


FIELDS = ("title", "description", "content", "requester_name", "reward",
          "occurrence_date", "time_alloted", "keywords","qualifications")
FIELDS_PRETTY = tuple(
        map(
            lambda s: " ".join(map(string.capitalize, s.split("_"))),
            FIELDS
        ))
FIELDS_PRETTY_DICT = dict(zip(FIELDS, FIELDS_PRETTY))
ORDERS = ("asc", "desc")
ORDERS_STRINGS = ("ascending", "descending")
SORT_BY_FIELDS = tuple(FIELDS[:7])
PAGE_SIZES = ("5", "10", "20", "50")
SEARCH_IN_CHOICES = zip(FIELDS, FIELDS_PRETTY)
SORT_BY_CHOICES = zip(map(lambda order: "{}_{}".format(order[0], order[1]),
                          product(ORDERS, SORT_BY_FIELDS)),
                      map(lambda order: "{} ({})".format(
                                FIELDS_PRETTY_DICT[order[1]],
                                order[0]),
                          product(ORDERS_STRINGS, SORT_BY_FIELDS)))
HITS_PER_PAGE_CHOICES = zip(PAGE_SIZES, PAGE_SIZES)

class HitGroupContentSearchForm(SearchForm):

    search_in = forms.MultipleChoiceField(
            choices=SEARCH_IN_CHOICES,
            required=False
        )
    sort_by = forms.ChoiceField(
            choices=SORT_BY_CHOICES,
            required=False,
        )
    hits_per_page = forms.ChoiceField(
            choices=HITS_PER_PAGE_CHOICES,
            required=False
        )

    def cleaned_data_or_empty(self):
        try:
            cleaned_data = self.cleaned_data
        except AttributeError:
            cleaned_data = { }
        return cleaned_data

    def search(self):
        search_queryset = super(HitGroupContentSearchForm, self).search()
        cleaned_data = self.cleaned_data_or_empty()
        query = cleaned_data.get("q", "")
        if not query:
            return search_queryset
        search_in = cleaned_data.get("search_in", FIELDS)
        sort_by = cleaned_data.get("sort_by", "asc_title").split("_")
        sort_by = "{}{}".format("" if sort_by[0] == "asc" else "-",
                                "_".join(sort_by[1:]))
        kwargs = {}
        for field in search_in:
            kwargs[field] = query
        search_queryset = search_queryset.filter_and(**kwargs)
        search_queryset = search_queryset.order_by(sort_by)
        return search_queryset

    def submit_url(self):
        cleaned_data = self.cleaned_data_or_empty()
        query = cleaned_data.get("q", "")
        search_in = "".join(map(lambda f: "&search_in={}".format(f),
                            cleaned_data.get("search_in", [])))
        sort_by = "".join(map(lambda o: "&sort_by={}".format(o),
                          [cleaned_data.get("sort_by", "title")]))
        hits_per_page = "".join(map(lambda hpp: "&hits_per_page={}".format(hpp),
                                [cleaned_data.get("hits_per_page", "5")]))
        return "?q={}{}{}{}".format(query, search_in, sort_by, hits_per_page)

    def hits_per_page_or_default(self):
        cleaned_data = self.cleaned_data_or_empty()
        try:
            hits_per_page = int(cleaned_data["hits_per_page"])
        except ValueError:
            hits_per_page = 5
        return hits_per_page
