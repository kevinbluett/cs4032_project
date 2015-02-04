from async.helpers import LithiumHelper
from util.thread_pool import LithiumThreadPool
import base64, os, pickle, hashlib

__author__ = 'kevin'


from base_service import BaseService

class FileService(BaseService):

    ALLOWED_ACTIONS = ["UPLOAD", "DOWNLOAD", "DELETE", "REPLICATE", "GET_FILE_INFO", "INVALIDATE_CACHE"]
    LOGGING_TAG = "FILE_SERVICE"

    def __init__(self, d_host, d_port):
        self.__bootstrap()
        self.d_host = d_host
        self.d_port = d_port

        # General thread pool to perform tasks to stop blocking actions on network interrupts
        self.thread_pool = LithiumThreadPool(5)

    def announce(self):
        """ Announces this fileserver to the directory server """
        self._raw_request(self.d_host, self.d_port, "ANNOUNCE_SERVER", (self.server_host, self.server_port), self.SERVER_SHARED_SECRET, self.ENCRYPTION_TYPE_INTERNAL)

    def upload(self, sock, filename, file_contents, *args):
        """ Methods allows a client proxy to upload a file to this specific file_server, which will
        then propagate the result afterwards. """
        path = filename.split("/")
        if not os.path.exists(".buckets/%s" % path[0]):
            os.makedirs(".buckets/%s" % path[0])

        with open(".buckets/%s" % filename, "wb") as file:
            file.write(file_contents)
            self.thread_pool.add_task(self.propagate_task, filename, file_contents)

        return ()

    def download(self, sock, filename, *args):
        """
            Returns the contents of a file to a user
        """
        # Check cache for file
        path = ".buckets/%s" % (filename)
        if not os.path.exists(path):
            pass # Try to retrieve file from replicated server

        with open(path, "rb") as file:
            # All data transports automatically base64 encoded no need to do here.
            return (file.read(),)

    def get_file_info(self, sock, filename, *args):
        """
            Checks if file exists on given filesrever and returns MD5 checksum
        """
        exists = os.path.exists(".buckets/%s" % filename)
        if exists:
            checksum = self.__file_checksum(filename)
        return (filename, exists, checksum)


    def propagate_task(self, filename, file):
        """
            Propagates a file to all servers in the network. File is only transferred if the file doesn't exist
            on the remote server already or if the MD5 of the remote file doesn't match.
        """
        raw = self._raw_request(self.d_host, self.d_port, "LIST_SERVERS", (), self.SERVER_SHARED_SECRET, "I")
        servers = pickle.loads(self.decrypt(base64.b64decode(raw.split(":")[2]), self.SERVER_SHARED_SECRET))
        md5 = self.__file_checksum(filename)

        for server in servers:
            if not (server[1] == self.server_host and server[2] == self.server_port):
                # fix to use local-loopback when running locally as external IP doesn't route correctly.
                host = "127.0.0.1" if (server[1] == self.server_host) else server[1]

                # Test checksum
                info = self._request(host, server[2], "GET_FILE_INFO", (filename,))

                # Only send replication request when file not remote fileserver or when checksums don't match
                if not bool(info[1]) or info[2] != md5:
                    self._raw_request(host, server[2], "REPLICATE", (filename, file), self.SERVER_SHARED_SECRET, "I")

    def replicate(self, sock, filename, file_contents, *args):
        self.thread_pool.add_task(self.replicate_task, filename, file_contents)
        return (True,)

    def replicate_task(self, filename, file_contents, *args):
        path = filename.split("/")
        if not os.path.exists(".buckets/%s" % path[0]):
            os.makedirs(".buckets/%s" % path[0])

        with open(".buckets/%s" % filename, "wb") as file:
            file.write(file_contents)

    def __bootstrap(self):
        if not os.path.exists(".buckets"):
             os.makedirs(".buckets")

    def __invalidate_caches(self, servers, filepath):
        for server in servers:
            self._raw_request(server[0], server[1], "INVALIDATE_CACHE", (filepath,))

    def __file_checksum(self, filepath):
        return hashlib.md5(open(".buckets/%s" % filepath, 'rb').read()).hexdigest()