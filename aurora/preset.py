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
        dict_rep = self.__dict__.copy()
        dict_rep.pop('displayable', 0)
        dict_rep.pop('task', 0)
        return dict_rep


class TransitionPreset(Preset):

    def __init__(self, new_presets, old_presets):
        self.new_presets = new_presets
        self.cancelled_presets = old_presets
        self.combined_channels = []
        self.combined_name = "transition"

        for preset in new_presets:
            self.combined_name += "-" + preset.name

        for preset in new_presets + old_presets:
            self.combined_channels.extend(preset.channels)

        payload = {
            'type': 'transition',
            'from': [p.as_dict() for p in old_presets],
            'to': [p.as_dict() for p in new_presets]
        }

        super(TransitionPreset, self).__init__(self.combined_name,
                                               self.combined_channels,
                                               payload,
                                               self.__create_transition())

    def start(self):
        self.task = asyncio.ensure_future(self.execute_then_replace())
        return self

    async def execute_then_replace(self):
        await self.displayable.display(self.channels)
        await lights.remove_presets([self], ignore_dropped=True)
        await lights.add_presets(self.new_presets)

    def __create_transition(self) -> Displayable:
        old_levels_dict = {}
        for cancelled_p in self.cancelled_presets:
            old_levels_dict.update(cancelled_p.displayable.get_current_levels())

        new_levels_dict = {}
        for new_p in self.new_presets:
            new_levels_dict.update(new_p.displayable.get_first_levels())

        for key, value in old_levels_dict.items():
            if key not in new_levels_dict:
                new_levels_dict[key] = 0

        for key, value in new_levels_dict.items():
            if key not in old_levels_dict:
                old_levels_dict[key] = 0

        old_levels = Levels(old_levels_dict)
        new_levels = Levels(new_levels_dict)

        return Fade([old_levels, new_levels], config.core.transition_duration, 1)

    def as_dict(self):
        dict_rep = super(TransitionPreset, self).as_dict()
        dict_rep.pop('new_presets', 0)
        dict_rep.pop('cancelled_presets', 0)
        dict_rep.pop('combined_channels', 0)
        dict_rep.pop('combined_name', 0)
        return dict_rep

