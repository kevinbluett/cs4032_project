__author__ = 'kevin'

import sqlite3, time, hashlib, base64
from random import random
from base_service import BaseService

class SecurityService(BaseService):

    ALLOWED_ACTIONS = ["LOGIN_REQUEST"]
    LOGGING_TAG = "SECURITY_SERVICE"
    DATABASE = "db.sqlite"

    def __init__(self):
        self.__create_tables()

    def login_request(self, sock, username, encrypted_request, *args):
        """ Performs the login request the user, returns ticket & session key encrypted with users password """
        user = self.__get_user(username)

        if user is not None and len(user) > 0:
            if self.decrypt(base64.b64decode(encrypted_request), str(user[0][1])) == "SECRET_LOGIN_REQUEST":
                session_key = self.__create_session(username, str(user[0][1]))
                ticket = self.encrypt(session_key, self.SERVER_SHARED_SECRET)
                return (True, "%s:%s" % (base64.b64encode(self.encrypt(session_key, str(user[0][1]))), base64.b64encode(ticket)))
            else:
                return (False,)

    def __get_user(self, username):
        return self._fetch_sql("select * from users where username=?", (username,))

    def __create_session(self, username, password):
        session_key = hashlib.sha256(username+str(time.time())+password).hexdigest()
        self._execute_sql("delete from sessions where username=?", (username,))
        self._execute_sql("insert into sessions (username, session_key) values (?, ?)", (username, session_key), exclusive=True)
        return session_key

    def __setup_demo(self):
        self._execute_sql("insert into users (username, password) values (?, ?)", ("demo", "demo"))

    def __create_tables(self):
        conn = sqlite3.connect(self.DATABASE)
        cur = conn.cursor()
        cur.executescript("""
            create table if not exists users(
                username TEXT,
                password TEXT
            );
            create table if not exists sessions(
                username TEXT,
                session_key TEXT
            );""")
        self.__setup_demo()