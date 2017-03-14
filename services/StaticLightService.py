import services.Service
import hardware_adapter
from log import setup_logger
import time

logger = setup_logger("Static Light Service")


class StaticLightService(services.Service.Service):

    def __init__(self):
        super().__init__()
        self.requires_gpio = True

    def run(self):
        hardware_adapter.enable_gpio()
        while True:
            self.mutex.acquire()
            next_preset = None if len(self.message_queue) == 0 else self.message_queue.pop()
            self.mutex.release()

            if next_preset is None:
                time.sleep(.0125)
            else:
                logger.info("Message Received. Type: " + next_preset['type'])
                if next_preset['type'] == 'color':
                    hardware_adapter.set_color(next_preset)
                elif next_preset['type'] == 'fade':
                    hardware_adapter.set_fade(next_preset)
                elif next_preset['type'] == 'sequence':
                    hardware_adapter.set_sequence(next_preset)

            self.mutex.acquire()
            if self.should_stop:
                break
            self.mutex.release()
        hardware_adapter.disable_gpio()
        logger.info("Thread cleanly stopped.")
