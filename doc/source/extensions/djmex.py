"""
    Django model sphinx autodoc plugin
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Using autodoc-process-docstring event to extend the model documentation.
    Additionally, django schema nodelist is build to display using
    djangomodelschema directive.

    Available settings:
    djmex_include_djangomodellists -- should djangomodellists be shown (False)
    djmex_pretty_model -- should django models be prettified (False)
    djmex_show_django_field -- show django field type along with db type (True)

"""

import inspect
import docutils
from sphinx.locale import _
from sphinx.util.compat import Directive
from django.utils.html import strip_tags
from django.utils.encoding import force_unicode
from django.db import models, connection


class djangomodellist(docutils.nodes.General, docutils.nodes.Element):
    pass


class DjangoModellistDirective(Directive):

    def run(self):
        return [djangomodellist('')]


def purge_nodes(app, env, docname):
    if not hasattr(env, 'djmex_all_djangomodels'):
        return
    env.djmex_all_djangomodels = [m for m in env.djmex_all_djangomodels
                                    if m['docname'] != docname]


def process_nodes(app, doctree, fromdocname):
    """Replaces all djangomodellist nodes with a list of the collected models.
    """

    env = app.builder.env
    content = []

    # generate representation
    if app.config.djmex_include_djangomodellists:

        for info in env.djmex_all_djangomodels:

            # title in the form
            # Table table_name (model_name)
            block = docutils.nodes.line_block()
            block.append(docutils.nodes.Text('Table '))
            block.append(docutils.nodes.strong(
                text=info['target']._meta.db_table))
            block.append(docutils.nodes.emphasis(
                text=' ({0})'.format(info['name'])))
            content.append(block)

            # add existing doc lines
            block = docutils.nodes.line_block()
            for l in info['lines']:
                para = docutils.nodes.paragraph()
                para.append(docutils.nodes.Text(l))
                block.append(para)
            content.append(block)

            # field list is represented as a single field containing a list
            field_list = docutils.nodes.field_list()
            field = docutils.nodes.field()
            field.append(docutils.nodes.field_name(text=_('Columns')))
            body = docutils.nodes.field_body()
            blist = docutils.nodes.bullet_list()
            body.append(blist)
            field.append(body)
            field_list.append(field)

            fields = info['target']._meta._fields()
            for field in fields:
                # adds field description in the form:
                # db_field_name (db_field_type[, django_field_type]) details
                # where details are: PK, Index, field.help_text
                db_column = field.db_column or field.name
                help_text = ' ' + strip_tags(force_unicode(field.help_text))
                try:
                    db_type = field.db_type(connection)
                except:
                    db_type = 'Unknown'

                if app.config.djmex_show_django_field:
                    ftype = ', '.join([db_type, field.get_internal_type()])
                else:
                    ftype = db_type

                db_index = ' Index' if field.db_index else ''
                is_pk = ' PK' if field.primary_key else ''

                para = docutils.nodes.paragraph()
                para += docutils.nodes.strong(text=db_column)
                para += docutils.nodes.emphasis(text=' ({0}) '.format(ftype))

                details = [is_pk, db_index, help_text]
                for i, d in enumerate(details):
                    if i > 0:
                        para += docutils.nodes.Text(' ', ' ')
                    para += docutils.nodes.Text(d, d)

                #name = docutils.nodes.field_name(text=db_column)
                li = docutils.nodes.list_item()
                li.append(para)
                blist.append(li)

            content.append(field_list)

    for node in doctree.traverse(djangomodellist):
        node.replace_self(content)


def add_djangomodel_node(app, what, name, obj, options, lines):
    """Stores target class for rendering in process nodes."""
    env = app.builder.env
    if not hasattr(env, 'djmex_all_djangomodels'):
        env.djmex_all_djangomodels = []

    env.djmex_all_djangomodels.append({
        'docname': env.docname,
        'target': obj,
        'name': name,
        'lines': [l for l in lines],
    })


def enrich_docstring(obj, lines):
    """Adds pretty model field listing to class description."""
    fields = obj._meta._fields()
    for field in fields:
        # Decode and strip any html out of the field's help text
        help_text = strip_tags(force_unicode(field.help_text))

        # Decode and capitalize the verbose name, for use if there isn't
        # any help text
        verbose_name = force_unicode(field.verbose_name).capitalize()

        if help_text:
            # Add the model field to the end of the docstring as a param
            # using the help text as the description
            lines.append(u':param %s: %s' % (field.attname, help_text))
        else:
            # Add the model field to the end of the docstring as a param
            # using the verbose name as the description
            lines.append(u':param %s: %s' % (field.attname, verbose_name))

        # Add the field's type to the docstring
        lines.append(u':type %s: %s' % (field.attname, type(field).__name__))


def process_docstring(app, what, name, obj, options, lines):
    """Gathers djangomodellist entries and enchances model docs for all django
    models processed.

    """
    if inspect.isclass(obj) and issubclass(obj, models.Model):

        # Add djangomodellist entry
        add_djangomodel_node(app, what, name, obj, options, lines)

        # Make pretty model description using verbose_names and help_text
        if app.config.djmex_pretty_model:
            lines = enrich_docstring(obj, lines)

    return lines


def setup(app):
    app.connect('autodoc-process-docstring', process_docstring)
    #app.connect('autodoc-process-signature', process_signature)

    # show model lists:
    app.add_config_value('djmex_include_djangomodellists', False, False)
    # settings to disable nice display of models fields
    app.add_config_value('djmex_pretty_model', False, False)
    # if true, django model field type will be shown together with db type
    app.add_config_value('djmex_show_django_field', True, False)
    # TODO: possible feature: exclude modules
    # app.add_config_value('djmex_excluded', [], False)

    app.add_node(djangomodellist)
    app.add_directive('djangomodellist', DjangoModellistDirective)
    app.connect('doctree-resolved', process_nodes)
    app.connect('env-purge-doc', purge_nodes)
