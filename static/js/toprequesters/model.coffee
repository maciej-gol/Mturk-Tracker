#
# Api for crud in the toprequesters view
#
class mtracker.toprequesters.model.Toprequester extends crud.model.Model
    urlRoot: '/top_requesters/api/toprequesters/'

class mtracker.toprequesters.collection.Toprequesters extends crud.collection.Collection
    model: mtracker.toprequesters.model.Toprequester
    urlRoot: '/top_requesters/api/toprequesters/'
    url: ->
        url = super
        # add report_type param
        joiner = if url.indexOf("?") isnt -1 then '&' else '?'
        report_type = $('input[name="report_type_hidden"]')[0].value
        url + joiner + "report_type=" + report_type
