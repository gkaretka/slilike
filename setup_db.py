import string

from clickhouse_driver import Client
from flask import Flask


def setup_db(app: Flask, table_name: string):
    # prepare database
    client = None

    while client is None:
        try:
            client = Client('clickhouse_db')
        except:
            app.logger.info("Error connecting to database! Reconnecting...")

    s_q = """
    CREATE TABLE IF NOT EXISTS """ + table_name + """
    (
    userid UInt64,
    rating Int8,
    datetime DateTime64(3, 'Europe/Prague'),
    sign Int8
    )
    ENGINE = CollapsingMergeTree(sign) ORDER BY userid;
    """

    client.execute(s_q)
    client.disconnect()
