$ ->

  hgcs = new crud.collection.HitGroupContentSearch

  hgcs.fetchMeta (meta) ->

    hgcTable = new crud.view.HitGroupContentSearchTable
      el: $('#hitgroupcontent-table')
      meta: meta
      collection: hgcs

    # hiding the select/deselect buttons
    hgcTable.removeWidget '.crud-meta-actions', 'crud.view.SelectAllWidget'
    hgcTable.removeWidget '.crud-meta-actions', 'crud.view.SelectNoneWidget'

    hgcTable.render()
    hgcs.fetch()

    fV = new crud.view.FilterList
        collection: hgcs
        filterGroups: meta.filterGroups
    $(".filter-bar").append fV.render().el

