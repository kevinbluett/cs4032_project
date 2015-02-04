__author__ = 'kevin'
import time
from threading import Lock

class CacheEntry(object):
    """ Used by the memory object cache in order to """
    def __init__(self, key, value):
        CacheEntry.__init__(self)
        self._key=key
        self._value=value
        self._timestamp = time.time()
        self._lock=Lock()

class MemoryObjectCache:
    """ Generic in memory cache that locks while contents are being written / read """
    def __init__(self):
        self.dict = dict()

    def insert(self, key, value, timestamp=None):
        """ Inserts object into the cache if the new element, or timestamp > than existing value. """
        if key not in dict:
            self.dict[key] = CacheEntry(value)
        elif timestamp:
            if timestamp > self.dict[key]._timestamp:
                self.dict[key]._lock.acquire()
                self.dict[key]._value = value
                self.dict[key]._timestamp = timestamp
                self.dict[key]._lock.release()

    def delete(self, key):
        """ Removes object from the cache when it is safe to do so """
        if key in self.dict:
            self.dict[key]._lock.acquire()
            del self.dict[key]

    def get(self, key):
        """ Returns the value of the element in the cache """
        if key in self.dict:
            self.dict[key]._lock.acquire()
            value = dict[key]._value
            self.dict[key]._lock.release()

            return value
        return None

    def invalidate_all(self):
        """ Safely deletes all values in the cache by ensuring that First come first served on the locks"""
        for x in dict:
            self.delete(x)