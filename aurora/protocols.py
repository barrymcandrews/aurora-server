import logging
import os
import asyncio
import aiofiles

log = logging.getLogger(__name__)


class AudioFilterProtocol(asyncio.Protocol):
    current_visualizer = None

    def __init__(self):
        super().__init__()
        self.complete_event = asyncio.Event()

    def connection_made(self, transport):
        log.debug('connection made')

    def data_received(self, data: bytes):
        if AudioFilterProtocol.current_visualizer is not None:
            for i in range(0, len(data), 2048):
                AudioFilterProtocol.current_visualizer.visualize(data[i:i+2048])

    def eof_received(self):
        log.debug("Audio EOF Received!")

    def connection_lost(self, exc):
        log.debug("Audio Connection Lost!")
        self.complete_event.set()

    def pause_writing(self):
        log.debug("Writing Paused!")

    def resume_writing(self):
        log.debug("Writing Resumed")


def create_fifo():
    if os.path.exists('/tmp/aurora-fifo'):
        os.remove('/tmp/aurora-fifo')
    os.mkfifo('/tmp/aurora-fifo', mode=0o777)
    os.chmod('/tmp/aurora-fifo', mode=0o777)
create_fifo()


async def read_fifo():
    create_fifo()
    loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
    afp = AudioFilterProtocol()
    while True:
        afp.complete_event.clear()
        audio_fifo = await aiofiles.open('/tmp/aurora-fifo', mode='r')
        await loop.connect_read_pipe(lambda: afp, audio_fifo)
        await afp.complete_event.wait()
