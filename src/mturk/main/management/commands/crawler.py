# -*- coding: utf-8 -*-

# Konrad Adamczyk (conrad.adamczyk at gmail.com)

# Changelog:
# 07.10.2009:	First release

##########################################################################################

# The program is written as an Amazon Mechanical Turk (mturk.com)
# crawler consisting of Crawler and Worker classes using specified
# callback functions.

from BeautifulSoup import BeautifulSoup, ResultSet
from django.core.management.base import BaseCommand
from django.db.models import Max
from multiprocessing import Pipe, Process
from threading import Thread

import datetime
import logging
import re
import sys
import time
import urllib2

from crawler_callbacks_data import callback_allhit, callback_details, callback_add_crawlfk
from crawler_callbacks_save import callback_database
from crawler_common import get_allhit_url, get_group_url
from mturk.main.models import Crawl

class Command(BaseCommand):
    help = 'Runs the MTurk crawler'
    args = 'number of crawling processes'

    def handle(self, processes_count, **options):
        processes_count = int(processes_count)
        crawler = Crawler(processes_count)
        crawler.start()
        crawler.join()


##########################################################################################
# Thread-based class running the mturk crawl. Makes use of Worker objects fired as 
# separate processes.
##########################################################################################
class Crawler(Thread):

    ######################################################################################
    # Contructor
    #
    # In:
    #  processes_count - number of Worker processes to fire during the crawl
    ######################################################################################
    def __init__(self, processes_count):
        Thread.__init__(self)
        
        self.processes_count = processes_count
        self.data = []
        self.errors = []


    ######################################################################################
    # Appends given list of errors to the overall list of errors that occured during crawl
    #
    # In:
    #  errors - list containing error objects
    ######################################################################################
    def append_errors(self, errors):
        for error in errors:
            self.errors.append(error)

    ######################################################################################
    # Fetches mturk.com and returns teh number of the furthermost page in the pagination.
    ######################################################################################
    def get_max_page(self):
        response = urllib2.urlopen(get_allhit_url())
        html = response.read()
        pattern = re.compile(r"<a href=\".*pageNumber=([0-9]+).{150,200}Last</a>")
        max_page = re.search(pattern, html)
        if max_page: return int(max_page.group(1))
        else:        return 1

    ######################################################################################
    # Launches Worker thread with a given job.
    #
    # In:
    #  callback		- function to execute
    #  callback_arg	- function's argument
    #  conn			- Pipe's child connection
    #  **kwargs
    ######################################################################################
    def launch_worker(self, callback, callback_arg, conn=None, **kwargs):
        worker = Worker(callback, callback_arg, **kwargs)
        worker.start()
        worker.join()
        if conn:
            conn.send({
                'data': worker.data,
                'errors': worker.errors
            })

    ######################################################################################
    # Divide's given work between processes_count number of processes, where work is 
    # defined as executing function with a list of values.
    #
    # Values given as the function's parameter are fairly distributed between a defined 
    # number of processes, and each process uses them as a parameter in it's callback 
    # function.
    #
    # In:
    #  values			- list of values to process
    #  callback			- function to execute
    #  processes_count	- number of processes to work with values
    #  **kwargs
    ######################################################################################
    def process_values(self, values, callback, processes_count=1, **kwargs):

        ##################################################################################
        # Retrieves data from Pipe's connection
        ##################################################################################
        def receive_from_pipe(conn):
            while True:
                if conn.poll(None):
                    data = conn.recv()
                    conn.close()
                    return data
                time.sleep(1)

        data = []
        errors = []

        conns = []
        processes = []

        max_value = len(values)-1
        interval = max_value/processes_count
        values_range = processes_count
        if processes_count*(interval+1) < max_value:
            values_range = values_range + 1

        values_from = 0
        values_to = interval if interval <= max_value else max_value

        for i in range(0, values_range):

            parent_conn, child_conn = Pipe(False)
            conns.append(parent_conn)

            processes.append(Process(target=self.launch_worker,
                                     args=(callback,values[values_from:values_to+1],
                                     child_conn), kwargs=kwargs))

            values_from = values_to + 1
            values_to = values_to + interval + 1
            if i == values_range-2 and values_to > max_value:
                values_to = max_value

        for process in processes: process.start()

        for conn in conns:
            result = receive_from_pipe(conn)
            for record in result['data']: data.append(record)
            for error in result['errors']: errors.append(error)

        for process in processes: process.join()

        return {
            'data': data,
            'errors': errors
        }

	######################################################################################
    def run(self):

        logging.debug('Crawler started')

        start_time = datetime.datetime.now()

		# Fetching data from every mturk.com HITs list page.
        result_allhit = self.process_values(range(1,2), callback_allhit, 
                                            self.processes_count)
        self.data = result_allhit['data']
        self.append_errors(result_allhit['errors'])

		# Fetching html details for every HIT group.
        result_details = self.process_values(self.data, callback_details, 
                                             self.processes_count)
        self.data = result_details['data']
        self.append_errors(result_details['errors'])

		# Logging crawl information into the database.
        success = True if len(self.data) > 0 else False
        
        crawl = Crawl(**{
            'start_time':           start_time,
            'end_time':             datetime.datetime.now(),
            'success':              success,
            'groups_downloaded':    len(self.data),
            #'errors':               str(self.errors) # !
            'errors':               ''
        })
        crawl.save()

        result_add_crawlfk = self.process_values(self.data, callback_add_crawlfk, 
                                                 crawl=crawl)
        self.data = result_add_crawlfk['data']
        self.append_errors(result_add_crawlfk['errors'])

		# Saving results in the database.
        result_save_database = self.process_values(self.data, callback_database)
        print self.errors

        logging.debug(
            "Crawler finished in %s with %d results and %d errors" % (
                (datetime.datetime.now()-start_time),
                len(self.data),
                len(self.errors)
            )
        )
        
##########################################################################################
# Thread-based class executing given function with certain parameters.
##########################################################################################
class Worker(Thread):

    ######################################################################################
    # Contructor.
    #
    # In:
    #  callback		- function to execute
    #  callback_arg	- function's argument
    #  **callback_kwargs
    ######################################################################################
    def __init__(self, callback, callback_arg, **callback_kwargs):
        Thread.__init__(self)

        self.callback = callback
        self.callback_arg = callback_arg
        self.callback_kwargs = callback_kwargs
        self.data = []
        self.errors = []

    def run(self):

        try:
            self.data, self.errors = self.callback(self.callback_arg, 
                                                   **self.callback_kwargs)
        except:
            import traceback
            logging.error('%s: %s' % (sys.exc_info()[0].__name__, sys.exc_info()[1]))
            self.errors.append({
                'type': str(sys.exc_info()[0].__name__),
                'value': str(sys.exc_info()[1]),
                'traceback': unicode(traceback.extract_tb(sys.exc_info()[2]))
            })
