from abc import abstractmethod
from asyncio import Task
from typing import Dict, List

import asyncio

from aurora_server.lights.pins import Device
from aurora_server.lights.visualizer import Visualizer

Level = Dict[str, int]
Fade = List[Level]


class Preset(object):

    def __init__(self):
        self.__devices: List[Device] = []
        self.__task: Task = None

    def add_device(self, device: Device):
        self.__devices.append(device)

    def remove_device(self, device: Device):
        self.__devices.remove(device)

    def get_devices(self) -> List[Device]:
        return self.__devices

    def start(self):
        self.__task = asyncio.ensure_future(self.execute)

    async def stop(self):
        self.__task.cancel()
        await self.__task

    @abstractmethod
    async def execute(self):
        pass


class LevelsPreset(Preset):

    def __init__(self, levels: Dict[str, int]):
        super().__init__()
        self.levels: Dict[str, int] = levels

    async def execute(self):
        for device in self.get_devices():
            for label, value in self.levels.items():
                device.set_pins_with_label(label, value)


class AudioPreset(Preset):

    def __init__(self, visualizer_class):
        super().__init__()
        self.__visualizer_class = visualizer_class
        self.__visualizer: Visualizer = None

    async def execute(self):
        return

    def get_visualizer(self):
        pass

