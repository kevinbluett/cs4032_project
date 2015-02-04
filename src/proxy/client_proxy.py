import socket, os, base64, pickle
from helpers import ProxyHelper, ClientBase

__author__ = 'kevin'


class ClientProxy(ClientBase):

    def __init__(self, s_host, s_port, d_host, d_port, f_host, f_port, l_host, l_port):
        self.s_host = s_host
        self.s_port = s_port
        self.d_host = d_host
        self.d_port = d_port
        self.f_host = f_host
        self.f_port = f_port
        self.l_host = l_host
        self.l_port = l_port
        self.__bootstrap()

        # Create client session with server
        self._auth_request("demo", "demo")

    def read(self, filepath):
        response = self._request(self.d_host, self.d_port, "SELECT_SERVER", (filepath,), self.session_key, "E")

        b64 = self._raw_request(self.f_host, self.f_port, "DOWNLOAD", (response[0],), self.session_key, "E")
        path = response[0].split("/")
        if not os.path.exists(".buckets/%s" % path[0]):
            os.makedirs(".buckets/%s" % path[0])

        with open(".buckets/%s" % response[0], "wb") as file:
            dencoded_string = base64.b64decode(b64)
            file.write(dencoded_string)

    def write(self, filepath):
        # Request a lock
        lock = self.request_lock(filepath)
        response = self._request(self.d_host, self.d_port, "SELECT_SERVER", (filepath,), self.session_key, "E")

        if len(response) == 0:
            # No file-servers available
            return False

        self.request_lock(response[0])

        file = open(filepath, "rb")
        self._request(self.f_host, self.f_port, "UPLOAD", (response[0], file.read()), self.session_key, "E")

        # Unlock file
        self.request_unlock(filepath, lock[2])


    def request_lock(self, filepath):
        return self._request(self.l_host, self.l_port, "LOCK_FILE", (filepath,), self.session_key, "E")

    def request_unlock(self, filepath, id):
        return self._request(self.l_host, self.l_port, "UNLOCK_FILE", (filepath, id), self.session_key, "E")

    def delete(self, filename):
        pass

    def __bootstrap(self):
        if not os.path.exists(".buckets"):
             os.makedirs(".buckets")




cb = ClientProxy("localhost", 5555, "localhost", 8888, "localhost", 7777, "localhost", 6666)
cb.read("dir1/kev.txt")
cb = ClientProxy("localhost", 5555, "localhost", 8888, "localhost", 7776, "localhost", 6666)
cb.write("dir1/kev.1txt")