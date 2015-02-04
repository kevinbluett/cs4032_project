from threading import Thread
import sqlite3, socket, base64
from itertools import cycle, izip

__author__ = 'kevin'

from async.server import *

class BaseService:

    SERVER_SHARED_SECRET = "SERVER_SECRET"
    ENCRYPTION_TYPE_INTERNAL = "I"
    ENCRYPTION_TYPE_EXTERNAL = "E"

    def start(self, port):
        """ Starts the server in another thread """
        self.server_port = port
        self.server_host = socket.gethostbyname(socket.gethostname())

        # Starts the service at the given port
        LithiumAsyncServer('0.0.0.0', int(port), self.handle_input, self.LOGGING_TAG)
        Thread(target=asyncore.loop, args=[]).start()

    def handle_input(self, server, (sock, addr)):
        sock.setblocking(True)

        wrapped_sock = SocketWrapper(sock)

        try:
            gen = wrapped_sock.readline()
            line = gen.next()
        except Exception, e:
            print str(e)

        if line is not None and len(line) > 0:
            args = line[:-1].split(":")
            self.handle_command(server, wrapped_sock, args[0], *args[1:])

    def handle_command(self, server, sock, method, *args):
        # Use "ALLOWED" methods in order to automagically execute correct method
        server.log("Handling command '%s'" % method)
        if method in self.ALLOWED_ACTIONS:
            f = getattr(self, method.lower())

            encryption_key = None
            encryption_type = args[0]
            if encryption_type == "E":
                message = base64.b64decode(args[1])
                ticket = base64.b64decode(args[2])

                encryption_key = self.decrypt(ticket, self.SERVER_SHARED_SECRET)
                args = self.decrypt(message, encryption_key).split(":")

            elif encryption_type == "I":
                encryption_key = self.SERVER_SHARED_SECRET
                args = self.decrypt(base64.b64decode(args[1]), encryption_key).split(":")
            else:
                encryption_type = None

            try:
                output = f(sock, *args)

                if output is not None:
                    sock.send("%s\n" % self.__prepare_tuple(method, output, encryption_key, encryption_type))
            except Exception, e:
                print str(e)
        else:
            raise NotImplementedError()

    def __prepare_tuple(self, method, data, encryption_key=False, encryption_type=None):
        """ Prepares a tuple for transport via socket """
        out = "%s:" % (method)

        if encryption_type:
            out = "%s%s:" % (out, encryption_type)

        concat = ""
        for x in data:
            concat += "%s:" % str(x)
        concat = concat[:-1]

        if encryption_key:
            return "%s%s" % (out, base64.b64encode(self.encrypt(concat, encryption_key)))
        else:
            return "%s%s" % (out, concat)


    def _request(self, server, port, method, data, encrypted=False):
        line = self._raw_request(server, port, method, data)

        if line is not None:
            args = line.split(":")[1:]

            #for i in xrange(len(args)):
            #    args[i] = arg#base64.b64decode(args[i])

            return args
        else:
            return None

    def _raw_request(self, server, port, method, data, encryption_key=False, encryption_type=None):
        """ Opens up a raw new socket to communicate data to the specified server + port combo """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server, port))
        sw = SocketWrapper(sock)
        sw.send("%s\n" % self.__prepare_tuple(method, data, encryption_key, encryption_type))
        line = sw.readline().next()
        sock.close()
        return line

    def _fetch_sql(self, cmd, args):
        """ Executes the fetch command on a specific SQL query """
        conn = sqlite3.connect(self.DATABASE)
        cur = conn.cursor()
        try:
            cur.execute(cmd, args)
            data = cur.fetchall()
            conn.commit()
            conn.close()
            return data
        except:
            return None

    def _execute_sql(self, cmd, args, exclusive=False):
        """ Executes given SQL with no return. Optional exclusivity over the SQL execution is available """
        conn = sqlite3.connect(self.DATABASE)
        if exclusive:
            conn.isolation_level = 'EXCLUSIVE'
            conn.execute('BEGIN EXCLUSIVE')

        cur = conn.cursor()
        try:
            cur.execute(cmd, args)
            conn.commit()
            conn.close()
            return True
        except Exception, e:
            return False

    def encrypt(self, message, key):
        return ''.join(chr(ord(c)^ord(k)) for c,k in izip(message, cycle(key)))

    def decrypt(self, cyphered, key):
        return ''.join(chr(ord(c)^ord(k)) for c,k in izip(cyphered, cycle(key)))