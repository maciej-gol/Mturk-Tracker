$ ->

  hgcs = new crud.collection.HitGroupContents

  hgcs.fetchMeta (meta) ->

    hgcTable = new crud.view.HitGroupContentTable
      el: $('#hitgroupcontent-table')
      meta: meta
      collection: hgcs

    hgcTable.render()
    hgcs.fetch()
