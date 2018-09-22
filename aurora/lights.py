from typing import List

from aurora import hardware
from aurora.configuration import Channel, Configuration
from aurora.preset import Preset, TransitionPreset

config: Configuration = Configuration()
presets: List[Preset] = []


async def add_presets(new_presets: List[Preset]):
    """Starts and adds each preset to the Global List."""

    for preset in new_presets:
        presets.append(preset.start())


async def put_preset(new_preset: Preset):
    await put_presets([new_preset])


async def put_presets(new_presets: List[Preset]):
    """Checks for conflicts then adds each preset.

    Checks whether the currently running presets are using channels that
    will be required by the new presets. If there are any conflicts the old
    preset will be stopped. Any channels that were used by a cancelled preset
    that aren't used by a new preset are set to off.

    """
    dropped_presets: List[Preset] = []
    dropped_channels: List[Channel] = []
    new_channels: List[Channel] = []

    for new_preset in new_presets:
        for running_preset in presets:

            # If the new preset has needs a channel that is in use
            if not set(running_preset.channels).isdisjoint(new_preset.channels):
                dropped_presets.append(running_preset)
                dropped_channels += set(running_preset.channels).difference(new_preset.channels)

        new_channels += new_preset.channels

    if config.core.enable_transitions:
        new_presets = [TransitionPreset(new_presets, dropped_presets)]

    await remove_presets(dropped_presets, ignore_dropped=True)
    await add_presets(new_presets)

    for dropped_channel in dropped_channels:
        hardware.set_pwm(dropped_channel.pin, 0)


async def remove_presets(running_presets: List[Preset], ignore_dropped=False):
    """Stops the given presets' tasks then removes them. Sets dropped channels to
    off unless ignore_dropped=True.
    """
    dropped_channels: List[Channel] = []
    cancelled_presets = running_presets.copy()

    for preset in running_presets:
        await preset.stop()
        dropped_channels.extend(preset.channels)
        presets.remove(preset)

    if not ignore_dropped:
        if config.core.enable_transitions:
            transition = TransitionPreset([], cancelled_presets)
            await add_presets([transition])
        else:
            for dropped_channel in dropped_channels:
                hardware.set_pwm(dropped_channel.pin, 0)


async def remove_presets_by_id(ids: List[int], ignore_dropped=False):
    """Removes presets from the list with any of the given ids.
    Sets dropped channels to off unless ignore_dropped=True.
    """

    matching_presets = [x for x in presets if x.id in ids]
    await remove_presets(matching_presets, ignore_dropped)


async def clear_presets():
    """Removes all presets from the list and sets their channels to off."""

    await remove_presets(presets)
    presets.clear()

