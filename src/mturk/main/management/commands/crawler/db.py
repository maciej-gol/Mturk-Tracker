# -*- coding: utf-8 -*-

import logging

from gevent import monkey
monkey.patch_all()
from gevent import socket

import psycopg2
from psycopg2 import extensions

from django.conf import settings



log = logging.getLogger('crawler.db')


def wait_callback(conn, timeout=None):
    while True:
        state = conn.poll()
        if state == extensions.POLL_OK:
            return
        elif state == extensions.POLL_READ:
            socket.wait_read(conn.fileno(), timeout=timeout)
        elif state == extensions.POLL_WRITE:
            socket.wait_write(conn.fileno(), timeout=timeout)
        else:
            log.error('Psycopg2 driver error. Bad result')
            raise psycopg2.OperationalError(
                "Bad result from poll: %r" % state)

# make postgresql driver work the async way
extensions.set_wait_callback(wait_callback)


class DB(object):

    def __init__(self):
        self.conn = psycopg2.connect('dbname=%s user=%s password=%s' % \
            (settings.DATABASE_NAME, settings.DATABASE_USER, settings.DATABASE_PASSWORD))
        self.curr = self.conn.cursor()

    def is_hitgroup_new(self, group_id):
        """Check if hitgroup with given ID already exists in db. Return True
        if not, else False
        """
        self.curr.execute('''
            SELECT 1 FROM main_hitgroupcontent WHERE group_id = %s
        ''', (group_id, ))
        # if len > 0, the group already exists in database
        return not bool(len(self.curr.fetchone()))

    def insert_hit_group_content(self, data):
        self.curr.execute('''
            INSERT INTO main_hitgroupcontent(
                reward, description, title, requester_name, qualifications,
                time_alloted, html, keywords, requester_id, group_id,
                group_id_hashed, occurrence_date, first_crawl_id
            )
            VALUES (
                %(reward)s, %(description)s, %(title)s, %(requester_name)s,
                %(qualifications)s, %(time_alloted)s, %(html)s, %(keywords)s,
                %(requester_id)s, %(group_id)s, %(group_id_hashed)s,
                %(occurrence_date)s, %(first_crawl_id)s
            )''', data)

    def insert_hit_group_status(self, data):
        self.curr.execute('''
            INSERT INTO main_hitgroupstatus (
                crawl_id, inpage_position, hit_group_content_id, page_number,
                group_id, hits_available, hit_expiration_date
            )
            VALUES (
                %(crawl_id)s, %(inpage_position)s, %(hit_group_content_id)s,
                %(page_number)s, %(group_id)s, %(hits_available)s,
                %(hit_expiration_date)s
            )''', data)