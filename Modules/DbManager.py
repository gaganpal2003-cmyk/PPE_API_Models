import sqlite3
from pathlib import Path
import json

import yaml


def adapt_list_to_JSON(lst):
    return json.dumps(lst).encode('utf8')


def convert_JSON_to_list(data):
    return json.loads(data.decode('utf8'))


sqlite3.register_adapter(list, adapt_list_to_JSON)
sqlite3.register_converter("json", convert_JSON_to_list)


class Databasemgr:
    def __init__(self, db_path):
        """ init database """
        self.DB = db_path

    def exceute(self, sqlstmt):
        with sqlite3.connect(self.DB, check_same_thread=False) as cnn:
            cursor = cnn.cursor()
            cursor.execute(sqlstmt)
            cnn.commit()
        return True

    # def insert(self, query, data):
    #     with sqlite3.connect(self.DB, check_same_thread=False) as cnn:
    #         cursor = cnn.cursor()
    #         cursor.execute(query, data)
    #         cnn.commit()
    #     return True
    def insert(self, query, data):
        try:
            with sqlite3.connect(self.DB, check_same_thread=False) as cnn:
                cursor = cnn.cursor()
                cursor.execute(query, data)
                cnn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error inserting data: {e}")
            return False

    def insert_many(self, query, data):
        try:
            with sqlite3.connect(self.DB, check_same_thread=False) as cnn:
                cursor = cnn.cursor()
                cursor.executemany(query, data)
                cnn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error inserting data: {e}")
            return False


    def select(self, sqlstmt):
        with sqlite3.connect(self.DB, check_same_thread=False) as cnn:
            cursor = cnn.cursor()
            cursor.execute(sqlstmt)
            cnn.commit()
        return cursor.fetchall()
