from aurora_server import configuration
from aurora_server.lights import light_manager
from janus import Queue

config = configuration.Configuration()
preset_queue = Queue()
light_manager.start_process(preset_queue)


def get_devices() -> dict:
    devices = dict()
    for d in config.hardware.devices:
        devices.update({
            d.name: {
                'hardware': d.data,
                'preset': d.preset
            }
        })

    return {'devices': devices}


def get_device(name) -> dict:
    devices = list()
    for d in config.hardware.devices:
        if d.name == name:
            devices.append({
                'hardware': d.data,
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
