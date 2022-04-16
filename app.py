import hashlib
import time
from datetime import datetime
from flask import Flask, render_template, request
from clickhouse_driver import Client

from setup_db import setup_db

# ratingsV2
# ratings
table_name = "SLILIKE.ratings"

app = Flask(__name__)
setup_db(app, table_name)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/results", methods=["GET"])
def view_results():
    client = Client("clickhouse_db")

    t1 = int(time.time() * 10000)

    avg_score = client.execute(
        "select AVG(S_SUM) from (select SUM(rating * sign) as S_SUM from " + table_name + " GROUP BY userid HAVING SUM(sign) > 0)")
    if len(avg_score) > 0:
        app.logger.info("Avg score: " + str(avg_score[0]))
    else:
        t2 = int(time.time() * 10000)
        context = {
            "empty": True,
            "render_time": str((t2 - t1) / 10.0),
        }

        return render_template("results.html", context=context)

    star_stats = client.execute(
        "SELECT COUNT(rating * sign), rating FROM " + table_name + " GROUP BY rating HAVING SUM(sign) > 0")

    data = client.execute(
        "select userid, SUM(rating * sign) from " + table_name + " GROUP BY userid HAVING SUM(sign) > 0 LIMIT 10")

    t2 = int(time.time() * 10000)

    starsum = 0
    for i in range(len(star_stats)):
        starsum += star_stats[i][0]

    context = {
        "avg_score": avg_score[0],
        "star_stats": star_stats,
        "star_stats_sum": starsum,
        "render_time": str((t2 - t1) / 10.0),
        "data": data,
    }

    return render_template("results.html", context=context)


@app.route("/vote/<name>", methods=["POST"])
def reg_vote(name):
    name_hash = int.from_bytes(hashlib.sha256(name.encode("ascii")).digest()[:8], "little")
    score = request.values.get("score")
    app.logger.info("Received rating: " + str(score) + " from: " + str(name))

    client = Client("clickhouse_db")
    rating = client.execute(
        "SELECT rating FROM " + table_name + " WHERE userid = %(name_hash)s GROUP BY rating HAVING SUM(sign) > 0",
        {"name_hash": str(name_hash)})

    # insert deletion row or skip
    if len(rating) > 0:
        if int(rating[0][0]) == int(score):
            app.logger.info("Score matches previous... skipping")
            return "OK"

        app.logger.info("Detected prev val. Deleting: " + str(rating) + " from: " + str(name))
        client.execute("INSERT INTO " + table_name + " VALUES", [[name_hash, int(rating[0][0]), datetime.now(), -1]])

    # insert row
    app.logger.info("Inserting: " + str(score) + " from: " + str(name))
    client.execute("INSERT INTO " + table_name + " VALUES", [[name_hash, int(score), datetime.now(), 1]])
    client.disconnect()

    return "OK"


if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)
