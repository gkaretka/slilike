import hashlib
import random
import string
from datetime import datetime

from clickhouse_driver import Client


def randomname(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


def read_query():
    client = Client('localhost')
    star_stats = client.execute(
        "SELECT COUNT(rating * sign), rating FROM SLILIKE.ratings GROUP BY rating HAVING SUM(sign) > 0")

    print(star_stats)


def insert_random_ratings(user_cnt, debug_window=1):
    client = Client('localhost')
    names = {}
    for i in range(user_cnt):

        name = randomname(random.randint(3, 15))
        while name in names:
            name = randomname(random.randint(3, 15))

        names[name] = 1

        name_hash = int.from_bytes(hashlib.sha256(name.encode('ascii')).digest()[:8], 'little')
        score = random.randint(1, 5)

        rating = client.execute(
            'SELECT rating FROM SLILIKE.ratings WHERE userid = %(name_hash)s GROUP BY rating HAVING SUM(sign) > 0',
            {'name_hash': str(name_hash)})

        # insert deletion row
        if len(rating) > 0:
            print("Detected prev val. Deleting: " + str(rating) + " from: " + str(name))
            client.execute("INSERT INTO SLILIKE.ratings VALUES", [[name_hash, int(rating[0][0]), datetime.now(), -1]])

        # insert row
        if i % debug_window == 0:
            print("Inserting: " + str(score) + " from: " + str(name))

        client.execute("INSERT INTO SLILIKE.ratings VALUES", [[name_hash, int(score), datetime.now(), 1]])

    client.disconnect()


#insert_random_ratings(100000, debug_window=1000)
read_query()
