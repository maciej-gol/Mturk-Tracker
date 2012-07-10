import string
from itertools import product

from django import forms
from haystack.forms import SearchForm


class HitGroupContentSearchForm(SearchForm):

    ORDERS = ("asc", "desc")
    ORDERS_STRINGS = ("ascending", "descending")

    FIELDS = ("title", "description", "content", "keywords", "requester_name",
              "reward", "qualifications", "occurence_date", "time_alloted")
    FIELDS_STRINGS = map(lambda s: "{}{}".format(s[0].upper(), s[1:]), FIELDS)
    FIELDS_STRINGS = map(
            lambda s: " ".join(map(string.capitalize, s.split("_"))),
            FIELDS
        )

    SEARCH_IN_CHOICES = zip(FIELDS, FIELDS_STRINGS)
    SORT_BY_CHOICES = zip(map(lambda order: "{}_{}".format(order[0], order[1]),
                              product(ORDERS, FIELDS)),
                          map(lambda order: "{} ({})".format(order[1], order[0]),
                              product(ORDERS_STRINGS, FIELDS_STRINGS)))
    PAGE_SIZES = ("5", "10", "20", "50")
    HITS_PER_PAGE_CHOICES = zip(PAGE_SIZES, PAGE_SIZES)

    search_in = forms.MultipleChoiceField(
            choices=SEARCH_IN_CHOICES,
            required=False
        )
    sort_by = forms.ChoiceField(
            choices=SORT_BY_CHOICES,
            required=False
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
        search_in = cleaned_data.get("search_in", self.FIELDS)
        sort_by = cleaned_data.get("sort_by", "asc_title").split("_")
        sort_by = "{}{}".format("" if sort_by[0] == "asc" else "-", sort_by[1])
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

    def search_in_selected(self):
        return self.cleaned_data_or_empty().get("search_in", [])

