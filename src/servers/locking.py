__author__ = 'kevin'

import sqlite3, time
from random import random
from base_service import BaseService

class LockingService(BaseService):

    ALLOWED_ACTIONS = ["LOCK_FILE", "UNLOCK_FILE"]
    LOGGING_TAG = "LOCKING_SERVICE"
    DATABASE = "db.sqlite"

    def __init__(self):
        pass

    def lock_file(self, sock, filepath, *args):
        id = hash(random())

        #TODO: Check if lock exists + Block
        self.__create_lock(filepath, id)

        return (True, filepath, id)

    def unlock_file(self, sock, filepath, id, *args):
        self.__delete_lock(filepath, id)

        return (True, filepath)

    def __create_lock(self, file_name, lock_id):
        self._execute_sql("insert into locks (file_name, lock_id, timestamp) values (?, ?, ?)", (file_name, str(lock_id), int(time.time())), exclusive=True)

    def __delete_lock(self, file_name, lock_id):
        self._execute_sql("delete from locks where file_name=? and lock_id=?", (file_name, str(lock_id)), exclusive=True)

    def __create_tables(self):
        conn = sqlite3.connect(self.DATABASE)
        cur = conn.cursor()
        cur.executescript("""
            create table if not exists locks(
                file_name TEXT,
                lock_id INTEGER,
                timestamp INTEGER
            );""")