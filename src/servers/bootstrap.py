__author__ = 'kevin'

from directory_service import DirectoryService
from files_service import FileService
from locking_service import LockingService
from security_service import SecurityService

class BootstrapService:

    def __init__(self):
        pass

    def start(self):

        D_HOST = "localhost"
        D_PORT = 8888

        d = DirectoryService()
        d.start(D_PORT)

        s = SecurityService()
        s.start(5555)

        f = LockingService()
        f.start(6666)

        f = FileService(D_HOST, D_PORT)
        f.start(7777)
        f.announce()

        f = FileService(D_HOST, D_PORT)
        f.start(7776)
        f.announce()

        f = FileService(D_HOST, D_PORT)
        f.start(7775)
        f.announce()

        f = FileService(D_HOST, D_PORT)
        f.start(7774)
        f.announce()


b = BootstrapService()
b.start()