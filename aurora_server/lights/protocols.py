import asyncio
from collections import Coroutine
from logging import Logger
from typing import List

from aurora_server.configuration import Configuration
from aurora_server.lights.preset import Preset, AudioPreset
from aurora_server.lights.visualizer import Visualizer
from aurora_server.log import setup_logger

log: Logger = setup_logger('protocols')
config: Configuration = Configuration()
visualizer: Visualizer = Visualizer(config.hardware.devices[0])
presets: List[Preset] = []


async def put_preset(new_preset: Preset):
    global presets, visualizer

    # Remove any presets that conflict with the incoming preset
    for current_preset in presets:

        # Ensure there is only ever one AudioPreset at a time
        if current_preset is AudioPreset and new_preset is AudioPreset:
            await __remove_preset(current_preset)
            continue

        # Remove devices with conflicting pins from other presets
        # Remove the preset if it has no devices
        for used_device in current_preset:
            for required_device in new_preset.get_devices():

                if required_device.conflicts_with(used_device):
                    current_preset.remove_device(used_device)
                    if len(current_preset.get_devices()) < 1:
                        await __remove_preset(current_preset)

    if new_preset is AudioPreset:
        visualizer = new_preset.get_visualizer()
    else:
        new_preset.start()
    presets.add(new_preset)


def __add_preset(preset):
    global presets, visualizer
    if preset is AudioPreset:
        visualizer = preset.get_visualizer()
    else:
        preset.start()
    presets.add(preset)


async def __remove_preset(preset):
    global presets, visualizer
    if preset is AudioPreset:
        visualizer = None
    else:
        await preset.stop()
    presets.remove(preset)


class AudioFilterProtocol(asyncio.Protocol):

    def __init__(self, callback: Coroutine):
        super().__init__()
        self.callback = callback
        self.__bytes = bytearray()

    def connection_made(self, transport):
        log.debug("Audio Connection Made!")

    def data_received(self, data: bytes):
        log.debug("Audio Data Received!")
        log.debug("Audio Data: " + str(len(data)))
        # self.__bytes += data
        # log.debug("Bytes in buffer: " + str(len(self.__bytes)))
        if visualizer is not None:
            # while len(self.__bytes) >= 2048:
            #     visualizer.visualize(bytes(self.__bytes[0:2048]))
            #     self.__bytes = self.__bytes[2049:]
            for i in range(0, len(data), 2048):
                visualizer.visualize(data[i:i+2048])

                # log.info("chunk: " + str())

    def eof_received(self):
        log.debug("Audio EOF Received!")

    def connection_lost(self, exc):
        log.debug("Audio Connection Lost!")
        asyncio.ensure_future(self.callback)

    def pause_writing(self):
        log.debug("Writing Paused!")

    def resume_writing(self):
        log.debug("Writing Resumed")


class PresetProtocol(asyncio.Protocol):

    def __init__(self, callback: Coroutine):
        super().__init__()
        self.callback: Coroutine = callback

    def connection_made(self, transport):
        log.debug("Connection Made!")

    def data_received(self, data):
        log.debug("Preset Received!")
        # TODO: Deserialize preset
        # set_preset(data)

    def eof_received(self):
        log.debug("EOF Received!")

    def connection_lost(self, exc):
        log.debug("Connection Lost!")
        asyncio.ensure_future(self.callback)
