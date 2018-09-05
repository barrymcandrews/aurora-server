from typing import List

from aurora import hardware
from aurora.configuration import Channel
from aurora.preset import Preset


presets: List[Preset] = []


async def add_presets(new_presets: List[Preset]):
    """Starts and adds each preset to the Global List."""

    for preset in new_presets:
        presets.append(preset.start())


async def put_presets(new_presets: List[Preset]):
    """Checks for conflicts then adds each preset.

    Checks whether the currently running presets are using channels that
    will be required by the new presets. If there are any conflicts the old
    preset will be stopped. Any channels that were used by a cancelled preset
    that aren't used by a new preset are set to off.

    """

    dropped_channels: List[Channel] = []

    for new_preset in new_presets:
        for new_channel in new_preset.channels:
            for running_preset in presets:
                if new_channel in running_preset.channels:
                    await running_preset.stop()
                    presets.remove(running_preset)
                    dropped_channels += running_preset.channels

    for new_preset in new_presets:
        for new_channel in new_preset.channels:
            if new_channel in dropped_channels:
                dropped_channels.remove(new_channel)

    await add_presets(new_presets)

    for dropped_channel in dropped_channels:
        hardware.set_pwm(dropped_channel.pin, 0)


async def remove_all_presets():
    """Removes all presets from the list and sets their channels to off."""

    for preset in presets:
        await preset.stop()
        for channel in preset.channels:
            hardware.set_pwm(channel.pin, 0)
    presets.clear()


async def remove_presets(ids: List[int]):
    """Removes presets from the list with any of the given ids and
    sets their channels to off.
    """

    dropped_channels: List[Channel] = []

    for preset in presets:
        if preset.id in ids:
            await preset.stop()
            for channel in preset.channels:
                dropped_channels.append(channel)
            presets.remove(preset)

    for dropped_channel in dropped_channels:
        hardware.set_pwm(dropped_channel.pin, 0)
