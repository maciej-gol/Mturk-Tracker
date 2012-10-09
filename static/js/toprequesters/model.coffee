#
# Api for crud in the toprequesters view
#
class mtracker.toprequesters.model.Toprequester extends crud.model.Model
    urlRoot: '/top_requesters/api/toprequesters/'

class mtracker.toprequesters.collection.Toprequesters extends crud.collection.Collection
    model: mtracker.toprequesters.model.Toprequester
    urlRoot: '/top_requesters/api/toprequesters/'
