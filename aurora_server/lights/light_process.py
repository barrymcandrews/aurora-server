import asyncio
import threading
from logging import Logger
from multiprocessing import Process

from janus import Queue

from aurora_server import log, configuration
from aurora_server.lights.device import Device
from aurora_server.lights.workers.static_worker import LightWorker

config: configuration.Configuration = configuration.Configuration()
devices: [Device] = config.hardware.devices
logger = log.setup_logger('Light Worker Process')


class LightProcess(threading.Thread):

    def __init__(self):
        super().__init__()
        self.daemon = True

        self.preset_queue = None
        self.loop = None
        self.workers: [LightWorker] = []

    def run(self):
        logger.info("Starting LWP...")

        # Set up new event loop for this process
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.loop = asyncio.get_event_loop()
        self.preset_queue = Queue()

        # Enable all devices
        for d in devices:
            d.enable()
        self.preset_queue.sync_q.put(config.lights.initial_preset)

        # Start Loop
        futures = [asyncio.ensure_future(self.main())]
        try:
            self.loop.run_until_complete(asyncio.wait(futures))
        except KeyboardInterrupt:
            pass
        finally:
            logger.debug("LWP is stopping")
            for d in devices:
                d.disable()
            self.loop.close()

    async def main(self):
        logger.info("Main Loop has started")
        while True:
            logger.info("Waiting for preset...")
            data = await self.preset_queue.async_q.get()
            logger.info("Preset received!")

            if 'type' in data:
                await self.stop_all_tasks()
                try:
                    self.workers.append(LightWorker(data, config.hardware.all_devices))
                except asyncio.CancelledError:
                    pass
            else:
                await self.stop_listed_tasks(data)
                for device_name, preset in data.items():
                    for device in devices:
                        if device.name == device_name:
                            self.workers.append(LightWorker(preset, device))

    async def stop_all_tasks(self):
        """Stops all async tasks in self.workers and waits for them to finish"""

        for worker in self.workers:
            worker.future.cancel()

        for worker in self.workers:
            await worker.future
            self.workers.remove(worker)

    async def stop_listed_tasks(self, data):
        """Stops async tasks in self.workers that require the devices in data"""

        preset_devices = []
        for name in data:
            preset_devices.append(name)

        for worker in self.workers:
            if worker.device.name in preset_devices or worker.device == config.hardware.all_devices:
                worker.future.cancel()

        for worker in self.workers:
            if worker.device.name in preset_devices or worker.device == config.hardware.all_devices:
                await worker.future
                self.workers.remove(worker)



