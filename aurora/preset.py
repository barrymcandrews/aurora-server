import asyncio
from typing import Dict, List

from sanic.exceptions import InvalidUsage

from aurora import displayables
from aurora.configuration import Configuration, Channel
from aurora.displayables import Displayable

config = Configuration()


class Preset:
    next_id: int = 0

    def __init__(self, d):
        try:
            Preset.next_id = Preset.next_id + 1
            self.id: int = Preset.next_id
            self.name: str = d['name']

            self.channels: List[Channel] = []
            if 'pins' in d:
                for pin in d['pins']:
                    self.channels.append(config.hardware.channels_dict[pin])
            elif 'channels' in d:
                for channel in d['channels']:
                    self.channels.append(Channel(channel))
            elif 'devices' in d:
                for channel in config.hardware.channels:
                    if channel.device in d['devices']:
                        self.channels.append(channel)
            else:
                raise KeyError()
            self.verify_pins()

            self.devices: List[str] = []
            for channel in self.channels:
                if channel.device not in self.devices:
                    self.devices.append(channel.device)

            self.payload: Dict = d['payload']
            self.displayable: Displayable = displayables.factory(self.payload)
            self.task: asyncio.Task = None
        except KeyError:
            raise InvalidUsage('Invalid payload syntax.')

    def verify_pins(self):
        for channel in self.channels:
            if channel not in config.hardware.channels:
                raise InvalidUsage('Pin ' + str(channel.pin) + ' not found.')

    def start(self):
        self.task = self.displayable.start(self.channels)
        return self

    async def stop(self):
        self.displayable.stop()
        if self.task is not None:
            self.task.cancel()
            await self.task
        else:
            print('Warning: preset ' + str(self.id) + ' has no task to stop.')

    def as_dict(self):
        dict_rep = self.__dict__.copy()
        dict_rep.pop('displayable', 0)
        dict_rep.pop('task', 0)
        return dict_rep




