from threading import Thread, Lock


class Service(Thread):
    """This acts as the parent class for every service"""

    def __init__(self):
        super().__init__()
        self.daemon = True
        self.requires_gpio = False
        self.mutex = Lock()
        self.should_stop = False
        self.message_queue = []
        self.public_vars = {}

    def stop(self):
        self.mutex.acquire()
        self.should_stop = True
        self.mutex.release()

    def message(self, payload):
        self.mutex.acquire()
        self.message_queue.append(payload)
        self.mutex.release()

    def request(self, var_name):
        obj = None
        self.mutex.acquire()
        if var_name in self.public_vars:
            obj = self.public_vars[var_name]
        self.mutex.release()
        return obj
