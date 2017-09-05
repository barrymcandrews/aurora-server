import asyncio
from typing import Dict, List
from aurora import displayables
from aurora.configuration import Configuration, Channel
from aurora.displayables import Displayable

config = Configuration()


class Preset:
    next_id: int = 0

    def __init__(self, d):
        Preset.next_id = Preset.next_id + 1
        self.id: int = Preset.next_id
        self.name: str = d['name']

        self.channels: List[Channel] = []
        for channel in d['pins']:
            self.channels.append(config.hardware.channels_dict[channel])

        self.payload: Dict = d['payload']
        self.displayable: Displayable = displayables.factory(self.payload)
        self.task: asyncio.Task = None

    def start(self):
        self.task = self.displayable.start(self.channels)
        return self

    async def stop(self):
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




