import asyncio
from logging import Logger
from multiprocessing import Process
from janus import Queue
from aurora_server import log, configuration
from aurora_server.lights.device import Device
from .workers.light_worker import LightWorker
from .workers.filter_worker import FilterWorker
from .workers.static_worker import StaticWorker

config: configuration.Configuration = configuration.Configuration()
devices: [Device] = config.hardware.devices
logger: Logger = log.setup_logger('lights.lp')

workers: [LightWorker] = []
preset_q: Queue = None
audio_q: Queue = None


def start_process(preset_queue, audio_queue) -> Process:
    process = Process(target=start_event_loop, args=(preset_queue, audio_queue))
    process.start()
    return process


def start_event_loop(preset_queue, audio_queue):
    global preset_q, audio_q

    preset_q = preset_queue
    audio_q = audio_queue
    for d in devices:
        d.enable()
    preset_queue.sync_q.put(config.lights.initial_preset)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(asyncio.gather(check_queue))


async def check_queue():
    global preset_q, workers

    logger.debug("Main Loop has started")
    while True:
        logger.debug("Waiting for preset...")
        data = await preset_q.async_q.get()
        logger.debug("Preset received!")

        if 'type' in data:
            await stop_all_tasks()
            worker_class = FilterWorker if data['type'] == 'audio' else StaticWorker
            workers.append(worker_class(data, config.hardware.all_devices))

        else:
            await stop_listed_tasks(data)
            for device_name, preset in data.items():
                worker_class = FilterWorker if preset['type'] == 'audio' else StaticWorker
                for device in devices:
                    if device.name == device_name:
                        workers.append(worker_class(preset, device))


async def stop_all_tasks():
    """Stops all async tasks in self.workers and waits for them to finish"""
    global workers

    for worker in workers:
        worker.future.cancel()

    for worker in workers:
        await worker.future
        workers.remove(worker)


async def stop_listed_tasks(data):
    """Stops async tasks in self.workers that require the devices in data"""

    global workers

    preset_devices = []
    for name in data:
        preset_devices.append(name)

    for worker in workers:
        if worker.device.name in preset_devices or worker.device == config.hardware.all_devices:
            worker.future.cancel()

    for worker in workers:
        if worker.device.name in preset_devices or worker.device == config.hardware.all_devices:
            await worker.future
            workers.remove(worker)

