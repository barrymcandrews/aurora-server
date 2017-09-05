import os
import asyncio
import aiofiles


class AudioFilterProtocol(asyncio.Protocol):
    current_visualizer = None

    def __init__(self):
        super().__init__()
        self.complete_event = asyncio.Event()

    def connection_made(self, transport):
        print('connection made')

    def data_received(self, data: bytes):
        if AudioFilterProtocol.current_visualizer is not None:
            for i in range(0, len(data), 2048):
                AudioFilterProtocol.current_visualizer.visualize(data[i:i+2048])

    def eof_received(self):
        print("Audio EOF Received!")

    def connection_lost(self, exc):
        print("Audio Connection Lost!")
        self.complete_event.set()

    def pause_writing(self):
        print("Writing Paused!")

    def resume_writing(self):
        print("Writing Resumed")


def create_fifo():
    if os.path.exists('/tmp/audio'):
        os.remove('/tmp/audio')
    os.mkfifo('/tmp/audio', mode=0o777)
    os.chmod('/tmp/audio', mode=0o777)
create_fifo()


async def read_fifo():
    create_fifo()
    loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
    afp = AudioFilterProtocol()
    while True:
        afp.complete_event.clear()
        audio_fifo = await aiofiles.open('/tmp/audio', mode='r')
        await loop.connect_read_pipe(lambda: afp, audio_fifo)
        await afp.complete_event.wait()
