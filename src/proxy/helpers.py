__author__ = 'kevin'
import socket, base64

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
    def __prepare_tuple(self, method, data):
        out = "%s:" % method
        for x in data:
            out += "%s:" % base64.b64encode(x)
        return out[:-1]

    def _request(self, server, port, method, data):
        line = self._raw_request(server, port, method, data)

        if line is not None:
            args = line.split(":")[1:]

            for i in xrange(len(args)):
                args[i] = base64.b64decode(args[i])

            return args
        else:
            return None

    def _raw_request(self, server, port, method, data):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server, port))
        sock.send("%s\n" % self.__prepare_tuple(method, data))
        line = ProxyHelper.recv_line(sock)
        sock.close()
        return line.replace("\n", "")