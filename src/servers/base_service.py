from threading import Thread
import sqlite3, socket, base64

__author__ = 'kevin'

from async.server import *

class BaseService:

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

            # Revert arguments back to usable form.
            for i in xrange(len(args)-1):
                args[i+1] = base64.b64decode(args[i+1])

            self.handle_command(server, wrapped_sock, args[0], *args[1:])

    def handle_command(self, server, sock, method, *args):
        # Use "ALLOWED" methods in order to automagically execute correct method
        server.log("Handling command '%s'" % method)
        if method in self.ALLOWED_ACTIONS:
            f = getattr(self, method.lower())
            try:
                output = f(sock, *args)

                if output is not None:
                    sock.send("%s\n" % self.__prepare_tuple(method, output))
            except Exception, e:
                print str(e)
        else:
            raise NotImplementedError()

    def __prepare_tuple(self, method, data):
        """ Prepares a tuple for transport via socket """
        out = "%s:" % method
        for x in data:
            out += "%s:" % base64.b64encode(str(x))
        return out[:-1]

    def _raw_request(self, server, port, method, data):
        """ Opens up a raw new socket to communicate data to the specified server + port combo """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server, port))
        sw = SocketWrapper(sock)
        sw.send("%s\n" % self.__prepare_tuple(method, data))
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