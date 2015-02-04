from Queue import Queue
from threading import Thread

class LithiumWorker(Thread):
    def __init__(self, connections):
        Thread.__init__(self)
        self.connections = connections
        self.daemon = True
        self.start()
    
    def run(self):
        while True:
            func, args, kargs = self.connections.get()
            func(*args, **kargs)
            self.connections.task_done()

class LithiumThreadPool:
    def __init__(self, num_threads):
        self.connections = Queue(num_threads)
        for _ in range(num_threads): LithiumWorker(self.connections)

    def add_task(self, func, *args, **kargs):
        self.connections.put((func, args, kargs))

    def shutdown(self):
        self.connections.join()