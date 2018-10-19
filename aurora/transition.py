import asyncio
import math
from dataclasses import dataclass
from typing import List

from aurora import lights, hardware
from aurora.configuration import Configuration
from aurora.displayables import Displayable
from aurora.preset import Preset

config = Configuration()


@dataclass
class Change(object):
    pin: int
    old_val: int
    new_val: int

    current_val: int = None
    fade_fn = None

    def num_changes(self):
        return abs(self.old_val - self.new_val)

    def set_fade_function(self, num_changes):
        self.current_val = self.old_val
        delta = (self.new_val - self.old_val) / num_changes
        self.fade_fn = lambda step: int(math.floor(float(self.old_val) + (delta * float(step))))

    def update_current_val(self, step):
        self.current_val = self.fade_fn(step)


class Transition(Displayable):

    def __init__(self, changes):
        super().__init__(1)
        self.changes: List[Change] = changes
        self.num_changes = max(self.changes, key=lambda change: change.num_changes()).num_changes()
        self.num_changes = 1 if self.num_changes == 0 else self.num_changes
        for ch in self.changes:
            ch.set_fade_function(self.num_changes)
        self.pause_time = config.core.transition_duration / self.num_changes

    async def display_step(self, _):
        for i in range(0, self.num_changes + 1):
            for j in range(0, len(self.changes)):
                change = self.changes[j]
                change.update_current_val(i)
                hardware.set_pwm(change.pin, change.current_val)
            await asyncio.sleep(self.pause_time)

    def get_current_level(self, pin):
        for change in self.changes:
            if change.pin == pin:
                return change.current_val


class TransitionPreset(Preset):

    def __init__(self, old_presets, new_presets):
        self.new_presets: List[Preset] = new_presets
        self.old_presets: List[Preset] = old_presets
        self.combined_channels = []
        self.combined_name = "transition"

        for preset in new_presets:
            self.combined_name += "-" + preset.name

        for preset in new_presets + old_presets:
            for channel in preset.channels:
                if channel not in self.combined_channels:
                    self.combined_channels.append(channel)

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
        changes = []

        for channel in self.combined_channels:
            pin = channel.pin
            old_val = 0
            new_val = 0

            for old_p in self.old_presets:
                if channel in old_p.channels:
                    if isinstance(old_p.displayable, Transition):
                        old_levels = old_p.displayable.get_current_level(channel.pin)
                    else:
                        old_levels = old_p.displayable.get_current_levels()
                    if channel.label in old_levels:
                        old_val = old_levels[channel.label]

            for new_p in self.new_presets:
                if channel in new_p.channels:
                    new_levels = new_p.displayable.get_first_levels()
                    if channel.label in new_levels:
                        new_val = new_levels[channel.label]

            changes.append(Change(pin, old_val, new_val))

        return Transition(changes)
