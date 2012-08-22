# -*- coding: utf-8 -*-
from south.v2 import SchemaMigration
from utils.sql import add_table_columns


class Migration(SchemaMigration):

    def forwards(self, orm):
        add_table_columns("hits_mv", (("classes", "int null")))

    def backwards(self, orm):
        # We do not allow to undo migration.
        pass


complete_apps = ['main']
