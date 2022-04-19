import hashlib
import random
import re
import string
import time
from datetime import datetime
from english_words import english_words_set

from clickhouse_driver import Client
from backend.constants import table_name, word_suffix


def randomname(length):
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(length))


def read_query():
    client = Client("localhost")
    star_stats = client.execute(
        "SELECT COUNT(rating * sign), rating FROM SLILIKE.ratings GROUP BY rating HAVING SUM(sign) > 0")

    print(star_stats)


def insert_random_ratings(user_cnt, debug_window=1):
    client = Client("localhost")
    names = {}
    for i in range(user_cnt):

        name = randomname(random.randint(3, 20))
        while name in names:
            name = randomname(random.randint(3, 20))

        names[name] = 1

        name_hash = int.from_bytes(hashlib.sha256(name.encode("ascii")).digest()[:8], "little")
        score = random.randint(1, 5)

        rating = client.execute(
            "SELECT rating FROM " + table_name + " WHERE userid = %(name_hash)s GROUP BY rating HAVING SUM(sign) > 0",
            {"name_hash": str(name_hash)})

        # insert deletion row
        if len(rating) > 0:
            print("Detected prev val. Deleting: " + str(rating) + " from: " + str(name))
            client.execute("INSERT INTO " + table_name + " VALUES", [[name_hash, int(rating[0][0]), datetime.now(), -1]])

        # insert row
        if i % debug_window == 0:
            print("Inserting: " + str(score) + " from: " + str(name))

        client.execute("INSERT INTO " + table_name + " VALUES", [[name_hash, int(score), datetime.now(), 1]])

    client.disconnect()


def insert_random_ratings_batch(user_cnt, batch_size=1000):
    client = Client("localhost")
    names = {}
    batch = []
    b_cnt = 0

    t1 = int(time.perf_counter() * 10000)
    for i in range(user_cnt):

        name = randomname(random.randint(3, 20))
        while name in names:
            name = randomname(random.randint(3, 20))

        names[name] = 1

        name_hash = int.from_bytes(hashlib.sha256(name.encode("ascii")).digest()[:8], "little")
        score = random.randint(1, 5)

        batch.append([name_hash, int(score), datetime.now(), 1])

        if i != 0 and i % batch_size == 0:
            print("Inserting batch: " + str(b_cnt))
            b_cnt += 1
            client.execute("INSERT INTO " + table_name + " VALUES", batch)
            batch = []

    client.execute("INSERT INTO " + table_name + " VALUES", batch)
    client.disconnect()

    t2 = int(time.perf_counter() * 10000)

    print("Inserting " + str(user_cnt) + " rows took " + str((t2 - t1) / 10.0) + " ms")


def insert_random_word_batch(user_cnt, word_cnt, unique_word_cnt, batch_size=10000):
    client = Client("localhost")
    names = {}
    batch = []
    b_cnt = 0

    word_list = []
    cnt = 0
    for j in enumerate(english_words_set):
        word_list.append(j[1])
        cnt += 1
        if cnt == unique_word_cnt:
            break

    t1 = int(time.perf_counter() * 10000)
    for i in range(user_cnt):

        name = randomname(random.randint(3, 20))
        while name in names:
            name = randomname(random.randint(3, 20))
        names[name] = 1

        name_hash = int.from_bytes(hashlib.sha256(name.encode("ascii")).digest()[:8], "little")

        for j in range(word_cnt):
            word = random.choice(word_list)
            word_to_proc = re.sub(r'[^a-z0-9]', '', word.lower())
            word_hash = int.from_bytes(hashlib.sha256(word_to_proc.encode("ascii")).digest()[:8], "little")
            batch.append([name_hash, str(word), word_hash, datetime.now()])

        if i != 0 and i % batch_size == 0:
            print("Inserting batch: " + str(b_cnt))
            b_cnt += 1
            client.execute("INSERT INTO " + table_name + word_suffix + " VALUES", batch)
            batch = []

    print("Inserting batch: final")
    client.execute("INSERT INTO " + table_name + word_suffix + " VALUES", batch)
    client.disconnect()

    t2 = int(time.perf_counter() * 10000)

    print("Inserting " + str(user_cnt) + " rows took " + str((t2 - t1) / 10.0) + " ms")


# 10k users, each inputs 10 words from 15 unique words
#insert_random_word_batch(10000, 10, 15)

# 100k users, each inputs 10 words from 15 unique words
#insert_random_word_batch(100000, 10, 15)

# insert random 2,000,000 ratings in batches of 10,000
#insert_random_ratings_batch(2000000, 10000)

# INEFFICIENT FOR HIGH AMOUNT OF DATA - insert 100 ratings one by one
#insert_random_ratings(100)

# INEFFICIENT FOR HIGH AMOUNT OF DATA - insert 100 ratings one by one, with debug window 1000 inserts
#insert_random_ratings(100000, debug_window=1000)

# read query
#read_query()
