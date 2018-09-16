from abc import abstractmethod
from asyncio import CancelledError
from copy import deepcopy
from typing import Dict, List
import asyncio
from sanic.exceptions import InvalidUsage
from aurora.configuration import Channel, Configuration
from aurora.protocols import AudioFilterProtocol

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
        self.repeats_forever = (repeats < 0)

    def increment_step(self):
        self.step = self.step + 1

    def reset_step(self):
        self.step = 0

    def start(self, channels) -> asyncio.Task:
        return asyncio.ensure_future(self.display(channels))

    def stop(self):
        pass

    async def get_first_levels(self):
        return {}

    async def get_final_levels(self):
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

    async def get_first_levels(self):
        return self.levels

    async def get_final_levels(self):
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

    async def get_first_levels(self):
        return self.items[0]

    async def get_final_levels(self):
        return self.items[len(self.items) - 1]

    async def display_step(self, channels):
        colors = deepcopy(self.items)

        num_loops = len(colors) - 1
        if num_loops > 0:
            for i in range(0, num_loops, 1):
                next_index = i + 1 if i < len(colors) - 1 else 0

                current_levels = colors[i]
                next_levels = colors[next_index]
                delta_levels = dict()
                num_changes = 0
                for label, value in current_levels.levels.items():
                    delta_levels[label] = next_levels.levels[label] - value
                    num_changes = max(num_changes, abs(delta_levels[label]))

                if num_changes == 0:
                    continue
                pause_time = self.delay / num_changes

                for j in range(0, num_changes):
                    for label, value in current_levels.levels.items():
                        if current_levels.levels[label] != next_levels.levels[label]:
                            current_levels.levels[label] += int(delta_levels[label] / abs(delta_levels[label]))

                    await current_levels.display_step(channels)
                    await asyncio.sleep(pause_time)


class Sequence(Displayable):
    def __init__(self, items: List[Displayable], delay: int, repeats: int):
        super().__init__(repeats)
        self.items = items
        self.delay = delay
        self.repeats = repeats

    async def get_first_levels(self):
        return self.items[0].get_first_levels()

    async def get_final_levels(self):
        return self.items[len(self.items) - 1].get_final_levels()

    async def display_step(self, channels):
        for item in self.items:
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
        AudioFilterProtocol.current_visualizer = Visualizer(channels, self.filter)
        # TODO: Fit number of channels to the number of frequencies 
        return None

    def stop(self):
        AudioFilterProtocol.current_visualizer = None

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
        payload.pop('type', 0)
        if disp_type == 'levels':
            return Levels(payload)

        elif disp_type == 'fade':
            items: List[Levels] = []
            for sub in payload['levels']:
                sub_disp = factory(sub, True)
                if type(sub_disp) is Levels:
                    items.append(sub_disp)
            return Fade(items, payload['delay'], repeats)

        elif disp_type == 'sequence':
            items: List[Displayable] = []
            for sub in payload['sequence']:
                items.append(factory(sub, True))
            return Sequence(items, payload['delay'], repeats)

        elif disp_type == 'visualizer':
            return VisualizerPreset(payload)

    except KeyError:
        raise InvalidUsage('Preset payload format is invalid.')
