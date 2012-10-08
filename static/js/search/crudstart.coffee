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
    meta.filterGroups[1].filterGroupClass = mtracker.search.view.MultiSelectFilterGroup
    meta.filterGroups[2].filterGroupClass = mtracker.search.view.MultiSelectFilterGroup

    fV = new mtracker.search.view.FilterList
        collection: hgcs
        filterGroups: meta.filterGroups
        filterGroupClass: mtracker.search.view.HorizontalFilterGroup
    $(".filter-bar").append fV.render().el

    # activate chosen plugin and bind change event
    $(".chzn-select").chosen().change (e) ->
        vals = $(e.target).val()
        # get get related to this filter and remove all filters
        if vals
            key = vals[0].split(':', 1)[0]
        else
            # fallback to any option if none is selected
            key = $(e.target).children('option')[0].value
        # remove
        hgcs.removeFilterByKey(key.split(':', 1)[0])

        # add active values
        _.each vals, (filter) -> hgcs.addFilter(filter)

        hgcs.fetch()

