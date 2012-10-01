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
