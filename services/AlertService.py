import services.Service
import time
from log import setup_logger
import service_controller as sc


class AlertService(services.Service.Service):

    def __init__(self):
        super().__init__()
        self.logger = setup_logger("Alert Service")

    def run(self):
        cont = True
        while cont:
            self.mutex.acquire()
            next_alert = None if len(self.message_queue) == 0 else self.message_queue.pop()
            self.mutex.release()

            if next_alert is None:
                time.sleep(.0125)
            else:
                self.logger.info("Received alert.")
                # an alert could potentially call the sc and message the static light service

            self.mutex.acquire()
            cont = not self.should_stop
            self.mutex.release()
