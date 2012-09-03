import time
import logging

from utils.sql import query_to_dicts, execute_sql, query_to_tuples

log = logging.getLogger(__name__)


def clean_duplicates():

    ids = query_to_dicts("select group_id from main_hitgroupcontent group by group_id having count(*) > 1;")

    for id in ids:

        log.info("Deleting duplicate group %s" % id['group_id'])

        execute_sql("""delete from main_hitgroupstatus where
                        hit_group_content_id  in (
                            select id from main_hitgroupcontent where id !=
                                (select min(id) from main_hitgroupcontent where group_id = '%s')
                        and group_id = '%s');
        """ % (id['group_id'], id['group_id']))

        execute_sql("""delete from main_hitgroupcontent where
                        id != (select min(id) from main_hitgroupcontent where group_id = '%s') and group_id = '%s'
                    """ % (id['group_id'], id['group_id']))

    execute_sql('commit;')


def calculate_first_crawl_id():

    progress = 10
    results = query_to_dicts("select id from main_hitgroupcontent where first_crawl_id is null")
    log.info('got missing ids results')
    for i, r in enumerate(results):
        log.info("\tprocessing %s" % r['id'])
        execute_sql("""update main_hitgroupcontent p set first_crawl_id =
            (select min(crawl_id) from main_hitgroupstatus where hit_group_content_id = p.id)
            where
                id = %s
        """ % r['id'])

        if i % progress == 0:
            execute_sql('commit;')
            log.info("updated %s main_hitgroupcontent rows with first_crawl_id" % i)

    execute_sql('commit;')


def update_diffs(limit=100):
    start_time = time.time()
    execute_sql("""
        UPDATE hits_mv
            SET hits_diff = diffs.hits_diff
        FROM
            (SELECT
                group_id, crawl_id,
                    hits_available -
                    COALESCE(lag(hits_available) over (partition BY group_id ORDER BY crawl_id), 0)
                    AS hits_diff
            FROM hits_mv
            WHERE
                hits_diff is NULL
            AND crawl_id in
                (SELECT DISTINCT crawl_id
                FROM hits_mv
                WHERE hits_diff is NULL
                ORDER BY crawl_id DESC LIMIT %s)

            ) AS diffs

        WHERE (diffs.group_id = hits_mv.group_id) AND (diffs.crawl_id = hits_mv.crawl_id);""",
        (int(limit), ))
    execute_sql('commit;')

    log.debug('Updated diffs for %s crawls in %s\n%s', limit, (time.time() - start_time))


def update_first_occured_agregates():

    missing_crawls = query_to_tuples("""select id from main_crawl p where p.success = true and not exists (select crawl_id from main_hitgroupfirstoccurences where crawl_id = p.id );""")

    for row in missing_crawls:

        crawl_id = row[0]
        log.info("inserting missing crawl into main_hitgroupfirstoccurences: %s" % crawl_id)

        execute_sql("""INSERT INTO
                main_hitgroupfirstoccurences (reward, group_content_id,
                    crawl_id, requester_name, group_status_id, occurrence_date,
                    requester_id, group_id, hits_available, id)
                    select
                        p.reward,
                        p.id,
                        q.crawl_id,
                        p.requester_name,
                        q.id,
                        p.occurrence_date,
                        p.requester_id,
                        p.group_id,
                        q.hits_available,
                        nextval('main_hitgroupfirstoccurences_id_seq'::regclass)
                    from main_hitgroupcontent p join main_hitgroupstatus q
                        on( p.first_crawl_id = q.crawl_id and q.hit_group_content_id = p.id )
                        where q.crawl_id = %s;""" % crawl_id)

        execute_sql('commit;')
