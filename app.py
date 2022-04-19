import hashlib
import re
import time
from datetime import datetime
from flask import Flask, render_template, request
from clickhouse_driver import Client

from backend.constants import table_name, word_suffix
from backend.wordcloud import create_word_cloud_from_data
from backend.setup_db import setup_db


app = Flask(__name__)
setup_db(app, table_name, word_suffix)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/results", methods=["GET"])
def view_results():
    client = Client("clickhouse_db")

    # rating results
    t1 = int(time.perf_counter() * 10000)
    avg_score = client.execute(
        "SELECT AVG(S_SUM) FROM (SELECT SUM(rating * sign) as S_SUM FROM " + table_name + " GROUP BY userid HAVING SUM(sign) > 0)")
    if len(avg_score) > 0:
        app.logger.info("Avg score: " + str(avg_score[0]))
    else:
        t2 = int(time.perf_counter() * 10000)
        context = {
            "empty": True,
            "render_time": str((t2 - t1) / 10.0),
        }

        return render_template("results.html", context=context)

    star_stats = client.execute(
        "SELECT COUNT(rating * sign), rating FROM " + table_name + " GROUP BY rating HAVING SUM(sign) > 0")
    data = client.execute(
        "SELECT userid, SUM(rating * sign) FROM " + table_name + " GROUP BY userid HAVING SUM(sign) > 0 LIMIT 10")
    t2 = int(time.perf_counter() * 10000)

    starsum = 0
    for i in range(len(star_stats)):
        starsum += star_stats[i][0]

    # word cloud results
    wt1 = int(time.perf_counter() * 10000)

    word_hash_cnt = {}
    words = client.execute(
        "SELECT word, count(word_unique_hash), word_unique_hash FROM " + table_name
        + word_suffix + " GROUP BY word_unique_hash, word ORDER BY word_unique_hash")

    app.logger.info("Selected " + str(len(words)) + " words from")

    all_words_cnt = 0
    for word, cnt, hsh in words:
        if word_hash_cnt.get(hsh, 0) == 0:
            word_hash_cnt[hsh] = [word, cnt]
            all_words_cnt += cnt
        else:
            word_hash_cnt[hsh] = [word, word_hash_cnt[hsh][1] + cnt]
            all_words_cnt += cnt

    words_str = ""
    for val in word_hash_cnt:
        for i in range(word_hash_cnt[val][1]):
            words_str += word_hash_cnt[val][0].replace(" ", "_") + " "

    wt1_0 = int(time.perf_counter() * 10000)
    word_cloud = create_word_cloud_from_data(words_str)
    wt2 = int(time.perf_counter() * 10000)

    context = {
        "avg_score": avg_score[0],
        "star_stats": star_stats,
        "star_stats_sum": starsum,
        "render_time": str((t2 - t1) / 10.0),
        "data": data,
        "table": table_name,
        "table_word": word_suffix,
        "word_cloud": word_cloud,
        "word_cloud_gen_time": str((wt2 - wt1) / 10.0),
        "word_cloud_query_time": str((wt1_0 - wt1) / 10.0),
        "word_cloud_unique_cnt": str(len(words)),
        "word_cloud_all_cnt": str(all_words_cnt),
    }

    return render_template("results.html", context=context)


@app.route("/vote/<name>", methods=["POST"])
def reg_vote(name):
    name_hash = int.FROM_bytes(hashlib.sha256(name.encode("ascii")).digest()[:8], "little")
    score = request.values.get("score")
    app.logger.info("Received rating: " + str(score) + " FROM: " + str(name))

    client = Client("clickhouse_db")
    rating = client.execute(
        "SELECT rating FROM " + table_name + " WHERE userid = %(name_hash)s GROUP BY rating HAVING SUM(sign) > 0",
        {"name_hash": str(name_hash)})

    # insert deletion row or skip
    if len(rating) > 0:
        if int(rating[0][0]) == int(score):
            app.logger.info("Score matches previous... skipping")
            return "OK"

        app.logger.info("Detected prev val. Deleting: " + str(rating) + " FROM: " + str(name))
        client.execute("INSERT INTO " + table_name + " VALUES", [[name_hash, int(rating[0][0]), datetime.now(), -1]])

    # insert row
    app.logger.info("Inserting: " + str(score) + " FROM: " + str(name))
    client.execute("INSERT INTO " + table_name + " VALUES", [[name_hash, int(score), datetime.now(), 1]])
    client.disconnect()

    return "OK"


@app.route("/word/<name>", methods=["POST"])
def reg_word(name):
    name_hash = int.from_bytes(hashlib.sha256(name.encode("ascii")).digest()[:8], "little")
    word = request.values.get("word")
    app.logger.info("Word received: " + str(word) + " FROM: " + str(name))

    # prepare word for hashing - lower + remove
    word_to_proc = re.sub(r'[^a-z0-9]', '', word.lower())
    word_hash = int.from_bytes(hashlib.sha256(word_to_proc.encode("ascii")).digest()[:8], "little")
    client = Client("clickhouse_db")

    # insert row
    client.execute("INSERT INTO " + table_name + word_suffix + " VALUES",
                   [[name_hash, str(word), word_hash, datetime.now()]])
    client.disconnect()

    return "OK"


if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)
