import asyncio

from aurora_server.log import setup_logger

logger = setup_logger("lights.workers.LightWorker")


class LightWorker(object):

    def __init__(self, preset, device):
        self.preset = preset
        self.device = device

    async def set_levels(self, preset):
        for label, value in preset.items():
            if label != 'type':
                self.device.set_label_level(label, value)

    async def set_off(self):
        self.device.set_off()

    async def set_fade(self, fade):
        delay = 1 if 'delay' not in fade else fade['delay']
        colors = [] if 'levels' not in fade else fade['levels']

        num_loops = len(colors) - 1
        if num_loops > 0:
            for i in range(0, num_loops, 1):
                next_index = i + 1 if i < len(colors) - 1 else 0

                current_levels = dict(colors[i])
                next_levels = colors[next_index]
                delta_levels = dict()
                num_changes = 0
                for label, value in current_levels.items():
                    delta_levels[label] = colors[next_index][label] - value
                    num_changes = max(num_changes, abs(delta_levels[label]))

                if num_changes == 0:
                    continue
                pause_time = delay / num_changes

                for j in range(0, num_changes):
                    for label, value in current_levels.items():
                        if current_levels[label] != next_levels[label]:
                            current_levels[label] += int(delta_levels[label] / abs(delta_levels[label]))

                    await self.set_levels(current_levels)
                    await asyncio.sleep(pause_time)

    async def set_sequence(self, sequence):
        delay = 1 if 'delay' not in sequence else sequence['delay']
        repeats = 1 if 'repeat' not in sequence else sequence['repeat']
        presets = [] if 'sequence' not in sequence else sequence['sequence']
        while repeats > 0:
            for effect in presets:
                if 'type' not in effect:
                    continue
                elif effect['type'] == 'levels':
                    await self.set_levels(effect)
                    await asyncio.sleep(delay)
                elif effect['type'] == 'fade':
                    await self.set_fade(effect)
                elif effect['type'] == 'sequence':
                    await self.set_sequence(effect)
            repeats -= 1
