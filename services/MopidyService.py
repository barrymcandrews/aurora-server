import services.Service
import subprocess
import time
import os

config_path = os.path.dirname(os.path.realpath(__file__)) + '/../config/mopidy.conf'


class MopidyService(services.Service.Service):

    def __init__(self):
        super().__init__()
        self.process = None

    def run(self):
        self.process = subprocess.Popen(['mopidy', '--config', config_path])

        cont = True
        while cont:
            time.sleep(.0125)
            self.mutex.acquire()
            cont = not self.should_stop
            self.mutex.release()

        self.process.terminate()

