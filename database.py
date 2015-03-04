__author__ = 'bawki'

import sqlite3
import time


class CatDb():
    def __init__(self):
        self.db = sqlite3.connect('pingcat.db')
        self.c = self.db.cursor()
        self.createTables()

    def createTables(self):
        configured = False
        self.c.execute("""SELECT name FROM sqlite_master WHERE type='table' AND name='pingdata';""")
        data = self.c.fetchall()
        for row in data:
            if row[0] == 'pingdata':
                configured = True

        if not configured:
            self.c.execute("""create table pingdata (
                date REAL,
                dst text,
                timeout int,
                count int,
                numDataBytes int,
                data BLOB )""")
            self.db.commit()
            self.c.fetchone()

    def newPingTest(self, dst, timeout, count, numDataBytes, data):
        self.c.execute("""INSERT INTO 'pingdata' VALUES (?, ?, ?, ?, ?, ?)""",
                       (time.time(), dst, timeout, count, numDataBytes, data))
        self.db.commit()