#
# Tables
#
class mtracker.toprequesters.view.ToprequestersTableRow extends crud.view.TableRow

class mtracker.toprequesters.view.ToprequestersTable extends crud.view.Table
    itemViewClass: mtracker.toprequesters.view.ToprequestersTableRow
    template: crud.template('ejs/toprequesters/table.ejs')
