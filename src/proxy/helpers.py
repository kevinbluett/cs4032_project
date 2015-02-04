__author__ = 'kevin'
import socket, base64
from itertools import cycle, izip

class ProxyHelper(object):
    @staticmethod
    def recv_line(sock):
        read = ''
        try:
            chars = []
            while True:
                a = sock.recv(1)
                if a != "\r":
                    chars.append(a)
                if a == "\n" or a == "":
                    return "".join(chars)
        except socket.error, e:
            if isinstance(e.args, tuple):
                if e[0] == socket.errno.EPIPE:
                   print "Detected remote disconnect"
                   raise e
            else:
                print "socket error ", e
        return read

class ClientBase:
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
            return "%s%s:%s" % (out, base64.b64encode(self.encrypt(concat, encryption_key)), base64.b64encode(self.ticket))
        else:
            return "%s%s" % (out, concat)

    def _auth_request(self, username, password):
        encrypted_request = base64.b64encode(self.encrypt("SECRET_LOGIN_REQUEST", password))
        response = self._request(self.s_host, self.s_port, "LOGIN_REQUEST", (username, encrypted_request))

        if bool(response[0]):
            self.session_key = self.decrypt(base64.b64decode(response[1]), password)
            self.ticket = base64.b64decode(response[2])

    def _request(self, server, port, method, data, encryption_key=False, encryption_type=None):
        line = self._raw_request(server, port, method, data, encryption_key, encryption_type)

        if line is not None:
            args = line.split(":")[1:]

            if len(args) > 0 and args[0] == "E":
                args = self.decrypt(base64.b64decode(args[1]), self.session_key).split(":")

            return args
        else:
            return None

    def _raw_request(self, server, port, method, data, encryption_key=False, encryption_type=None):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server, port))
        sock.send("%s\n" % self.__prepare_tuple(method, data, encryption_key, encryption_type))
        line = ProxyHelper.recv_line(sock)
        sock.close()
        return line.replace("\n", "")


    def encrypt(self, message, key):
        return ''.join(chr(ord(c)^ord(k)) for c,k in izip(message, cycle(key)))

    def decrypt(self, cyphered, key):
        return ''.join(chr(ord(c)^ord(k)) for c,k in izip(cyphered, cycle(key)))