from clickhouse_driver import Client
from flask import Flask


def setup_db(app: Flask, table_name, word_suffix):
    # prepare database
    client = None

    while client is None:
        try:
            client = Client('clickhouse_db')
        except Exception as e:
            app.logger.error("Error connecting to database! Reconnecting...")
        finally:
            app.logger.info("Database running... setting up")

    app.logger.info("Creating database if not exists")
    s_q = """
    CREATE DATABASE IF NOT EXISTS SLILIKE
    """
    client.execute(s_q)
    app.logger.info("Done creating database")

    app.logger.info("Creating table " + table_name + " if not exists")
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
    app.logger.info("Done creating table" + table_name)

    app.logger.info("Creating table " + table_name + word_suffix + " if not exists")
    s_q = """
    CREATE TABLE IF NOT EXISTS """ + table_name + word_suffix + """
    (
    userid UInt64,
    word String,
    word_unique_hash UInt64, 
    datetime DateTime64(3, 'Europe/Prague')
    )
    ENGINE = MergeTree() ORDER BY word_unique_hash;
    """
    client.execute(s_q)
    app.logger.info("Done creating table" + table_name + word_suffix)

    client.disconnect()
