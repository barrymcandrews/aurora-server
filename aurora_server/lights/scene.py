from typing import List
from aurora_server.lights.pins import Device
from aurora_server.lights.preset import Preset
from aurora_server.lights.visualizer import Visualizer

all_devices: List[Device] = []
used_devices: List[Device]
visualizer: Visualizer = None


def set_preset(preset: Preset):
    pass
