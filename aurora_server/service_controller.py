from multiprocessing import Manager

from janus import Queue

from aurora_server import configuration
from aurora_server.audio import sources
from aurora_server.lights import aurora_daemon

config = configuration.Configuration()

manager = Manager()
preset_queue = Queue()
audio_queue = Queue()
aurora_daemon.start_process(preset_queue, audio_queue)


def get_devices() -> dict:
    devices = dict()
    for d in config.hardware.devices:
        devices.update({
            d.name: {
                'hardware': d.channels,
                'preset': d.preset
            }
        })

    return {'devices': devices}


def get_device(name) -> dict:
    devices = list()
    for d in config.hardware.devices:
        if d.name == name:
            devices.append({
                'hardware': d.channels,
                'preset': d.preset
            })
    if len(devices) != 1:
        return {'error': 'A device with that name was not found.'}
    return {name: devices[0]}


def set_devices(data) -> dict:
    # TODO: Check structure
    # TODO: remove items that aren't in that device

    for d in config.hardware.devices:
        for name, preset in data.items():
            if 'type' in data:
                d.preset = data
            elif d.name == name:
                d.preset = preset
    preset_queue.sync_q.put(data)
    return get_devices()


def get_sources() -> dict:
    return {
        'sources': list(sources.audio_sources.keys()),
        'active': sources.active_source
    }


def set_sources(data) -> dict:
    if 'active' in data and (data['active'] in sources.audio_sources or data['active'] == 'none'):
        sources.start_source(data['active'])

    return get_sources()
