#
# Tables
#
class mtracker.search.view.HitGroupContentSearchTableRow extends crud.view.TableRow
    template: crud.template('ejs/search/table_row.ejs')

class mtracker.search.view.HitGroupContentSearchTable extends crud.view.Table
    itemViewClass: mtracker.search.view.HitGroupContentSearchTableRow
    template: crud.template('ejs/search/table.ejs')

#
# Filters
#
class mtracker.search.view.HorizontalFullTextSearchItem extends crud.view.FullTextSearchItem
    tagName: 'div'

class mtracker.search.view.HorizontalFilterGroup extends crud.view.FilterGroup
    appendTo: 'div'
    attributes: { class: 'span row' }
    template: crud.template('ejs/search/horizontal_filter_group.ejs')

    filterWidgets = _.extend crud.view.standardFilterWidgets, {
        text: mtracker.search.view.HorizontalFullTextSearchItem
    }

class mtracker.search.view.MultiSelectFilterItem extends crud.view.ChoiceFilterItem
    tagName: 'option'
    template: crud.template('ejs/search/multi_select.ejs')

    attributes: -> { 'value': this.options.filter.key }

class mtracker.search.view.MultiSelectFilterGroup extends crud.view.FilterGroup
    appendTo: 'select'
    attributes: { class: 'span row'}
    template: crud.template('ejs/search/multi_select_group.ejs')

    filterWidgets: _.extend(crud.view.standardFilterWidgets, {
        choice: mtracker.search.view.MultiSelectFilterItem
    })

class mtracker.search.view.FilterList extends crud.view.FilterList
    attributes: { class: 'row fluid' }
