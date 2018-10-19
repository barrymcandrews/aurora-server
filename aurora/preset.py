import asyncio
from typing import Dict, List, Set

from sanic.exceptions import InvalidUsage

from aurora import displayables, lights
from aurora.configuration import Configuration, Channel
from aurora.displayables import Displayable, Levels, Fade

config = Configuration()


class Preset(object):
    next_id: int = 0

    def __init__(self, name, channels, payload, displayable):
        Preset.next_id = Preset.next_id + 1
        self.id: int = Preset.next_id
        self.name: str = name
        self.channels: List[Channel] = channels
        self.devices: List[str] = []
        self.payload: Dict = payload
        self.displayable: Displayable = displayable
        self.task: asyncio.Task = None

        # Generate affected devices
        for channel in self.channels:
            if channel.device not in self.devices:
                self.devices.append(channel.device)

    @classmethod
    def from_dictionary(cls, d):
        try:
            name: str = d['name']
            channels: List[Channel] = []
            payload: Dict = d['payload']
            displayable: Displayable = displayables.factory(payload)

            # Convert pins and device fields into channels
            if 'pins' in d:
                for pin in d['pins']:
                    channels.append(config.hardware.channels_dict[pin])
            elif 'channels' in d:
                for channel in d['channels']:
                    channels.append(Channel(channel))
            elif 'devices' in d:
                for channel in config.hardware.channels:
                    if channel.device in d['devices']:
                        channels.append(channel)

            # Verify that the channels exist on the Raspberry Pi
            for channel in channels:
                if channel not in config.hardware.channels:
                    raise InvalidUsage('Pin ' + str(channel.pin) + ' not found.')

            # Ensure preset has at least one valid channel
            if len(channels) == 0:
                raise InvalidUsage('You must supply at least one valid channel.')

            return Preset(name, channels, payload, displayable)

        except KeyError:
            raise InvalidUsage('Invalid payload syntax.')

    def start(self):
        self.task = self.displayable.start(self.channels)
        return self

    async def stop(self):
        self.displayable.stop()
        if self.task is not None:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        else:
            print('Warning: preset ' + str(self.id) + ' has no task to stop.')

    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "channels": self.channels,
            "devices": self.devices,
            "payload": self.payload
        }