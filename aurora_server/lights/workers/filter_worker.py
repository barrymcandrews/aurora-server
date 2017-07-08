import asyncio

from aurora_server.lights.filter import Filter
from aurora_server.log import setup_logger
from .light_worker import LightWorker

logger = setup_logger("lights.workers.FilterWorker")


class FilterWorker(LightWorker):

    def __init__(self, preset, device):
        super().__init__(preset, device)
        self.filter = Filter(device)

    async def run(self):
        try:
            self.filter.process_audio()
        except asyncio.CancelledError:
            pass
