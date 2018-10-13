import os
import asyncio
import aiofiles
import alsaaudio
import multiprocessing
from aurora.configuration import Configuration

config = Configuration()
debug = config.core.debug
chunk_size = config.audio.chunk_size


class AudioFifoProtocol(asyncio.BufferedProtocol):
    current_visualizer = None

    def __init__(self):
        super().__init__()
        self.complete_event = asyncio.Event()
        self.buffer = bytearray()
        self.larger_buffer = bytearray()

    def connection_made(self, transport):
        if debug:
            print('Audio FIFO Protocol: Connection Made')

    def get_buffer(self, sizehint):
        self.buffer = bytearray(max(sizehint, chunk_size))
        if len(self.buffer) < sizehint:
            self.buffer.extend(0 for _ in range(sizehint - len(self.buffer)))
        return self.buffer

    def buffer_updated(self, nbytes):
        self.larger_buffer = self.larger_buffer + self.buffer[:nbytes]
        while len(self.larger_buffer) >= chunk_size:
            chunk = self.larger_buffer[:chunk_size]
            del self.larger_buffer[:chunk_size]
            if AudioFifoProtocol.current_visualizer is not None:
                AudioFifoProtocol.current_visualizer.visualize(chunk)

    def eof_received(self):
        if debug:
            print('Audio FIFO Protocol: EOF Received')

    def connection_lost(self, exc):
        if debug:
            print('Audio FIFO Protocol: Connection Lost')
        self.complete_event.set()

    def pause_writing(self):
        if debug:
            print('Audio FIFO Protocol: Writing Paused')

    def resume_writing(self):
        if debug:
            print('Audio FIFO Protocol: Writing Resumed')


def create_fifo(path):
    if os.path.exists(path):
        os.remove(path)
    os.mkfifo(path, mode=0o777)
    os.chmod(path, mode=0o777)


async def read_fifo():
    afp = AudioFifoProtocol()
    loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()

    fifo_path = config.audio.fifo_path
    create_fifo(fifo_path)

    if config.audio.play_audio:
        fifo_path = '/tmp/aurora-fifo-chunked'
        create_fifo('/tmp/aurora-fifo-chunked')
        audio_player = multiprocessing.Process(target=play_audio)
        audio_player.start()

    while True:
        afp.complete_event.clear()
        audio_fifo = await aiofiles.open(fifo_path, mode='r')
        await loop.connect_read_pipe(lambda: afp, audio_fifo)
        await afp.complete_event.wait()


def play_audio():
    fifo_in_path = config.audio.fifo_path
    fifo_out_path = '/tmp/aurora-fifo-chunked'
    output_device = alsaaudio.PCM(alsaaudio.PCM_PLAYBACK, alsaaudio.PCM_NORMAL)
    output_device.setchannels(config.audio.audio_channels)
    output_device.setrate(config.audio.sample_rate)
    output_device.setformat(alsaaudio.PCM_FORMAT_S16_LE)
    output_device.setperiodsize(config.audio.chunk_size)
    while True:
        try:
            print('Audio Player: Attempting connection...')
            with open(fifo_in_path, 'rb') as in_fifo:
                print('Audio Player: Connected to source')
                with open(fifo_out_path, 'wb') as out_fifo:
                    print('Audio Player: Connected to sink')
                    while True:
                        data = in_fifo.read(config.audio.chunk_size)
                        out_fifo.write(data)
                        output_device.write(data)
        except IOError:
            print('Audio Player: Connection lost')
