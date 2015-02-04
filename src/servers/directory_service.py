import hashlib
import pickle

__author__ = 'kevin'

from base_service import BaseService
import os.path
import sqlite3

class DirectoryService(BaseService):

    ALLOWED_ACTIONS = ["SELECT_SERVER", "LIST_SERVERS", "ANNOUNCE_SERVER", "RETIRE_SERVER", "CREATE_DIR", "DELETE_DIR"]

    DATABASE = "db.sqlite"
    LOGGING_TAG = "DIRECTORY_SERVICE"

    def __init__(self):
        if not os.path.exists(self.DATABASE):
            self.__create_tables()

    def select_server(self, sock, filepath, *args):
        (path, file) = os.path.split(filepath)
        (name, ext) = os.path.splitext(file)
        hash = "%s/%s%s" % (hashlib.sha256(path).hexdigest(), name, ext)

        server = self.__find_directory_host(hash)

        if not server:
            server = self.__select_random_server()
            self.__insert_directory_host(hash, server[0][0])

        server = self.__select_server(server[0][1])
        return (hash, server[0][1], server[0][2])

    def announce_server(self, sock, host, port, *args):
        self._execute_sql("insert into servers (host, port) values (?, ?)", (host, port), exclusive=True)
        return (True,)

    def retire_server(self, sock, host, port, *args):
        self._execute_sql("delete from servers where host=? and port=?", (host, port))

    def list_servers(self, sock, *args):
        return (pickle.dumps(self._fetch_sql("select * from servers", ())), "PADDING")

    def __server_exists(self, host, port):
        return len(self._fetch_sql("select * from servers where host=? and port=?",(host, port))) != 0

    def __select_random_server(self):
        return self._fetch_sql("select * from servers where id >= (abs(random()) % (SELECT max(id) FROM servers));", ())

    def __select_server(self, id):
        return self._fetch_sql("select * from servers where id=?", (str(id),))

    def __find_directory_host(self, directory):
        return self._fetch_sql("select * from directories where directory=?", (directory,))

    def __insert_directory_host(self, directory, server_id):
        self._execute_sql("insert into directories (directory, server_id) values (?, ?)", (directory, str(server_id)))

    def __create_tables(self):
        conn = sqlite3.connect(self.DATABASE)
        cur = conn.cursor()
        cur.executescript("""
            create table servers(
                id INTEGER PRIMARY KEY ASC,
                host TEXT,
                port INTEGER
            );
            create table directories(
                directory,
                server_id INTEGER
            );""")