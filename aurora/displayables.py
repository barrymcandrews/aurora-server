import math
from abc import abstractmethod
from asyncio import CancelledError
from copy import deepcopy
from typing import Dict, List
import asyncio
from sanic.exceptions import InvalidUsage
from aurora.configuration import Channel, Configuration
from aurora.protocols import AudioFifoProtocol

import pyximport
pyximport.install()
from aurora.visualizer.visualizer import Visualizer
from aurora import hardware

config = Configuration()
pins: List[int] = []
for channel in config.hardware.channels:
    pins.append(channel.pin)
hardware.enable(pins)


class Displayable(object):

    def __init__(self, repeats):
        self.step = 0
        self.total_steps = repeats
        self.repeats_forever = (repeats <= 0)

    def increment_step(self):
        self.step = self.step + 1

    def reset_step(self):
        self.step = 0

    def start(self, channels) -> asyncio.Task:
        return asyncio.ensure_future(self.display(channels))

    def stop(self):
        pass

    def get_first_levels(self):
        return {}

    def get_current_levels(self):
        return {}

    async def display(self, channels):
        try:
            while self.repeats_forever or self.step < self.total_steps:
                await self.display_step(channels)
                self.increment_step()
        except CancelledError:
            raise CancelledError
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        finally:
            self.reset_step()

    @abstractmethod
    async def display_step(self, channels):
        pass


class Levels(Displayable):
    def __init__(self, levels: Dict[str, int]):
        super().__init__(repeats=1)
        self.levels: Dict[str, int] = levels
        for label, value in levels.items():
            if not (0 <= value <= 100):
                raise InvalidUsage('Level value not in range.')

    def get_first_levels(self):
        return self.levels

    def get_current_levels(self):
        return self.levels

    async def display_step(self, channels):
        for label, value in self.levels.items():
            for ch in channels:
                if ch.label == label:
                    hardware.set_pwm(ch.pin, value)


class Fade(Displayable):
    def __init__(self, items: List[Levels], delay: int, repeats: int):
        super().__init__(repeats)
        self.items = items
        self.delay = delay
        self.repeats = repeats
        self.current_levels: Levels = self.items[0]

    def get_first_levels(self):
        return self.items[0].levels

    def get_current_levels(self):
        return self.current_levels.levels

    async def display_step(self, channels):
        colors = deepcopy(self.items)

        num_loops = len(colors) - 1
        for i in range(0, num_loops, 1):
            next_index = i + 1 if i < len(colors) - 1 else 0

            self.current_levels = colors[i]
            next_levels = colors[next_index]
            delta_levels = dict()
            num_changes = 0
            for label, value in self.current_levels.levels.items():
                delta_levels[label] = next_levels.levels[label] - value
                num_changes = max(num_changes, abs(delta_levels[label]))

            if num_changes == 0:
                continue

            color_fns = {}
            for label, value in self.current_levels.levels.items():
                color_fns[label] = Fade.__create_fade_fn(next_levels.levels[label], value, num_changes)

            pause_time = self.delay / num_changes
            for j in range(0, num_changes + 1):
                for label in self.current_levels.levels:
                    self.current_levels.levels[label] = color_fns[label](j)

                await self.current_levels.display_step(channels)
                await asyncio.sleep(pause_time)

    @staticmethod
    def __create_fade_fn(finish, start, num_changes):
        delta = (finish - start) / num_changes
        return lambda step: int(math.floor(float(start) + (delta * float(step))))


class Sequence(Displayable):
    def __init__(self, items: List[Displayable], delay: int, repeats: int):
        super().__init__(repeats)
        self.items = items
        self.delay = delay
        self.repeats = repeats
        self.current_item: Displayable = self.items[0]

    def get_first_levels(self):
        return self.items[0].get_first_levels()

    def get_current_levels(self):
        return self.current_item.get_current_levels()

    async def display_step(self, channels):
        for item in self.items:
            self.current_item = item
            await item.display(channels)
            if isinstance(item, Levels):
                await asyncio.sleep(self.delay)


class VisualizerPreset(Displayable):
    def __init__(self, vis):
        super().__init__(repeats=1)
        self.visualizer = None
        self.filter = None
        for f in config.filters:
            if f.name == vis['filter']:
                self.filter = f
        if self.filter is None:
            self.filter = config.Filter(None)

    def start(self, channels):
        if self.filter.custom_channel_frequencies != 0:
            num_frequency_bins = len(self.filter.custom_channel_frequencies) - 1
            if len(channels) != num_frequency_bins:
                raise KeyError('This filter requires exactly ' + str(num_frequency_bins) + ' channels.')

        AudioFifoProtocol.current_visualizer = Visualizer(channels, self.filter)
        return None

    def stop(self):
        AudioFifoProtocol.current_visualizer = None

    async def display(self, channels: List[Channel]):
        pass

    async def display_step(self, channels):
        pass


def factory(p: Dict[str, any], nested=False) -> Displayable:
    payload = deepcopy(p)

    try:
        # when repeats is set to -1 the displayable should loop forever
        # if no repeat amount is specified it will default to 1 unless it is the root
        repeats = -1 if not nested else 1
        repeats = p['repeats'] if 'repeats' in p else repeats

        disp_type = payload['type'].lower()

        if disp_type == 'levels':
            return Levels(payload['levels'])

        elif disp_type == 'fade':
            items: List[Levels] = []
            for sub in payload['children']:
                sub_disp = factory(sub, True)
                if type(sub_disp) is Levels:
                    items.append(sub_disp)
            return Fade(items, payload['delay'], repeats)

        elif disp_type == 'sequence':
            items: List[Displayable] = []
            for sub in payload['children']:
                items.append(factory(sub, True))
            return Sequence(items, payload['delay'], repeats)

        elif disp_type == 'visualizer':
            return VisualizerPreset(payload['visualizer'])

    except KeyError:
        raise InvalidUsage('Preset payload format is invalid.')
