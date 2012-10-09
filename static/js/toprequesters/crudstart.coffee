$ ->

  trs = new mtracker.toprequesters.collection.Toprequesters

  trs.fetchMeta (meta) ->

    trTable = new mtracker.toprequesters.view.ToprequestersTable
      el: $('#toprequesters-table')
      meta: meta
      collection: trs

    trTable.render()
    trs.fetch()
