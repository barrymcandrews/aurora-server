from aurora_server import configuration
from aurora_server.lights.light_process import LightProcess

config = configuration.Configuration()
lightWorkerProcess = LightProcess()
lightWorkerProcess.start()


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
    lightWorkerProcess.preset_queue.sync_q.put(data)
    return get_devices()
