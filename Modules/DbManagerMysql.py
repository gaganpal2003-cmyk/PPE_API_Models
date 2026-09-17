import mysql.connector
from mysql.connector import Error
import json


def adapt_list_to_JSON(lst):
    return json.dumps(lst)


def convert_JSON_to_list(data):
    return json.loads(data)


class DatabaseMysqlmgr:
    def __init__(self, database):
        """Initialize MySQL connection parameters"""
        self.host = "localhost"
        self.user = "root"
        self.password = "cairo$123"
        self.database = database

    def get_connection(self):
        return mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database
        )

    def execute(self, sqlstmt):
        try:

            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(sqlstmt)
            conn.commit()
            conn.close()
            return True
        except Error as e:
            print(f"During execution Error executing statement: {e}")
            return False

    def insert(self, query, data):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, data)
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Error as e:
            print(f" During insert Error inserting data: {e}")
            return False

    def insert_many(self, query, data_list):
        """
        Insert multiple rows at once using executemany.
        :param query: SQL Insert statement with placeholders
        :param data_list: List of tuples containing data
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.executemany(query, data_list)
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Error as e:
            print(f" During insert_many Error inserting data: {e}")
            return False


    def select(self, sqlstmt):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(sqlstmt)
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except Error as e:
            print(f"Error selecting data: {e}")
            return []

# dbMysqlManager = DatabaseMysqlmgr("app")
# tb = dbMysqlManager.select("SHOW TABLES;")
# print(tb)