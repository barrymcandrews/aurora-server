import errno
import os
import threading
from logging import Logger

from janus import Queue

from aurora_server import log
from aurora_server import configuration

logger: Logger = log.setup_logger('audio.fifo')
config: configuration.Configuration = configuration.Configuration()
reader_thread: threading.Thread = None
is_open: bool = False


def create():
    logger.info('Making FIFO(s)')
    if os.path.exists(config.lights.fifo_path):
        os.remove(config.lights.fifo_path)
    os.mkfifo(config.lights.fifo_path, mode=0o777)
    os.chmod('/tmp/audio', mode=0o777)


def remove():
    os.remove(config.lights.fifo_path)


def start_reading() -> Queue:
    global reader_thread
    output_queue = Queue()
    reader_thread = threading.Thread(target=read, daemon=True, args=(output_queue,))
    reader_thread.start()
    return output_queue


def read(output_queue: Queue):
    while True:
        try:
            fifo = os.open(config.lights.fifo_path, os.O_RDONLY | os.O_NONBLOCK)
            while True:
                try:
                    data = os.read(fifo, config.lights.chunk_size)
                    output_queue.sync_q.put(data)
                except OSError as err:
                    if err.errno == errno.EAGAIN or err.errno == errno.EWOULDBLOCK:
                        continue
        except IOError:
            continue
