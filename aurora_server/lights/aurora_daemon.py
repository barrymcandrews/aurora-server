#!/usr/bin/env python3.6

import asyncio
import aiofiles
from logging import Logger
from multiprocessing import Process

import uvloop
from aurora_server.configuration import Configuration
from aurora_server.lights import pins
from aurora_server.lights.protocols import AudioFilterProtocol, PresetProtocol
from aurora_server.log import setup_logger
from aurora_server import fifo

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
config: Configuration = Configuration()
log: Logger = setup_logger('Light Manager')

audio_fifo_location: str = '/tmp/audio'


def start_process() -> Process:
    process = Process(target=main)
    process.daemon = True
    process.name = 'aurorad'
    process.start()
    return process


def main():

    pins.enable(config.hardware.all_pins)
    fifo.create()

    loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
    asyncio.ensure_future(open_audio_fifo())
    # asyncio.ensure_future(open_preset_fifo())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        log.info('Shutting down...')
        loop.stop()
        pins.disable()

async def open_audio_fifo():
    loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
    audio_fifo = await aiofiles.open(config.lights.fifo_path, mode='r')
    log.debug('*** opened audio fifo')
    afp = AudioFilterProtocol(callback=open_audio_fifo())
    await loop.connect_read_pipe(lambda: afp, audio_fifo)


async def open_preset_fifo():
    loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
    audio_fifo = await aiofiles.open(config.lights.fifo_path, mode='r')
    log.debug('*** opened light fifo')
    ap = PresetProtocol(callback=open_preset_fifo())
    await loop.connect_read_pipe(lambda: ap, audio_fifo)


if __name__ == '__main__':
    log.debug('Aurora Light Manager Daemon')
    log.debug('Starting main...')
    main()
