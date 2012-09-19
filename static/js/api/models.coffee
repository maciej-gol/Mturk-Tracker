# Full HitGroupContent api
class crud.model.HitGroupContent extends crud.model.Model
    urlRoot: '/api/hitgroupcontent/'

class crud.collection.HitGroupContents extends crud.collection.Collection
    model: crud.model.HitGroupContent
    urlRoot: '/api/hitgroupcontent/'

class crud.view.HitGroupContentTableRow extends crud.view.TableRow
    # empty

class crud.view.HitGroupContentTable extends crud.view.Table
    itemViewClass: crud.view.HitGroupContentTableRow

# Search view HitGroupContent api - contains a limited subset of fields
class crud.model.HitGroupContentSearch extends crud.model.Model
    urlRoot: '/api/hitgroupcontentsearch/'

class crud.collection.HitGroupContentSearch extends crud.collection.Collection
    model: crud.model.HitGroupContentSearch
    urlRoot: '/api/hitgroupcontentsearch/'

class crud.view.HitGroupContentSearchTableRow extends crud.view.TableRow
    template: crud.template('ejs/search/table_row.ejs')

class crud.view.HitGroupContentSearchTable extends crud.view.Table
    itemViewClass: crud.view.HitGroupContentSearchTableRow
    template: crud.template('ejs/search/table.ejs')
