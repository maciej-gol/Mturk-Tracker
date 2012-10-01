$ ->

  hgcs = new mtracker.search.model.HitGroupContentSearch

  hgcs.fetchMeta (meta) ->

    hgcTable = new mtracker.search.view.HitGroupContentSearchTable
      el: $('#hitgroupcontent-table')
      meta: meta
      collection: hgcs

    # hiding the select/deselect buttons
    hgcTable.removeWidget '.crud-meta-actions', 'crud.view.SelectAllWidget'
    hgcTable.removeWidget '.crud-meta-actions', 'crud.view.SelectNoneWidget'
    hgcTable.addWidget '.crud-meta-actions', 'crud.view.SorterSelect'

    hgcTable.render()
    hgcs.fetch()

    # override the default widgets
    meta.filterGroups[0].filterGroupClass = mtracker.search.view.MultiSelectFilterGroup
    meta.filterGroups[1].filterGroupClass = mtracker.search.view.MultiSelectFilterGroup

    fV = new mtracker.search.view.FilterList
        collection: hgcs
        filterGroups: meta.filterGroups
        filterGroupClass: mtracker.search.view.HorizontalFilterGroup

    $(".filter-bar").append fV.render().el

    # activate chosen plugin
    $(".chzn-select").chosen()
    $(".filter-bar").append()
