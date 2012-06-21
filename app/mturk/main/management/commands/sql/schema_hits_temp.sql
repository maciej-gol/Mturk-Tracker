--
-- Intermediate table used by diffs generating procedures.
--
-- For more details refer to hits_temp_population description in the
-- documentation under Database->Stored procedures
--
-- Name: hits_temp; Type: TABLE; Schema: public; Owner: postgres; Tablespace:
--

CREATE TABLE hits_temp (
    hits integer,
    group_id1 character varying(50),
    group_id2 character varying(50),
    crawl_id integer,
    prev_crawl_id integer
);


--
-- Name: onhits; Type: INDEX; Schema: public; Owner: postgres; Tablespace:
--

CREATE INDEX onhits ON hits_temp USING btree (hits);


--
-- Name: onhits_grpid2_crawlid; Type: INDEX; Schema: public; Owner: postgres; Tablespace:
--

CREATE INDEX onhits_grpid2_crawlid ON hits_temp USING btree (group_id2, crawl_id, hits);


--
-- Name: onhits_grpid2_pcrawlid; Type: INDEX; Schema: public; Owner: postgres; Tablespace:
--

CREATE INDEX onhits_grpid2_pcrawlid ON hits_temp USING btree (group_id2, prev_crawl_id, hits);


--
-- Name: onhits_grpid_crawlid; Type: INDEX; Schema: public; Owner: postgres; Tablespace:
--

CREATE INDEX onhits_grpid_crawlid ON hits_temp USING btree (group_id1, crawl_id, hits);


--
-- Name: onhits_grpid_pcrawlid; Type: INDEX; Schema: public; Owner: postgres; Tablespace:
--

CREATE INDEX onhits_grpid_pcrawlid ON hits_temp USING btree (group_id1, prev_crawl_id, hits);
