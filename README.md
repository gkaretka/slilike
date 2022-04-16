### SLike (Super Like)

Test of ClickHouse using `flask` + `mymarilyn/clickhouse-driver`. Fast setup thanks 
to `docker compose`.

### How to run:

- Install docker
- Run `docker-compose up` and enjoy

Flask application runs on 8080. ClickHouse uses default port configuration. This example is not 
what clickhouse is truly good at (large quantities of immutable data) but it gets job done anyway.
ClickHouse table is using `CollapsingMergeTree` so rows can be removed. This table engine is most 
suitable for this application (easy setup for data modification/deletion).

Application stores "ratings" for some random poll. These can be modified, each user can vote only
once (no login check, just type your nickname :) ). Results present average score, number of 
ratings for each category and first 10 ratings. 
