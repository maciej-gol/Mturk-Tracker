#
# Api for crud in the search view
#
class mtracker.search.model.HitGroupContentSearch extends crud.model.Model
    urlRoot: '/api/hitgroupcontentsearch/'

class mtracker.search.model.HitGroupContentSearch extends crud.collection.Collection
    model: mtracker.search.model.HitGroupContentSearch
    urlRoot: '/api/hitgroupcontentsearch/'
    multi_field_ordering: true
