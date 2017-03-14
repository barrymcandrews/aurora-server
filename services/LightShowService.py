import subprocess
import audioop
import os
import numpy as np
import errno
import RunningStats
from collections import deque

import fft
import hardware_adapter
import services.Service
from log import setup_logger

FIFO_PATH = '/tmp/audio'
GPIO_LEN = 3

ATTENUATE_PCT = 50.
SD_LOW = .4
SD_HIGH = .85
DECAY_FACTOR = 0
DELAY = 1.0
CHUNK_SIZE = 2048
SAMPLE_RATE = 48000
MIN_FREQUENCY = 20
MAX_FREQUENCY = 15000
CUSTOM_CHANNEL_MAPPING = 0
CUSTOM_CHANNEL_FREQUENCIES = 0
INPUT_CHANNELS = 2

hardware_adapter.enable_gpio()

config_path = os.path.dirname(os.path.realpath(__file__)) + '/../config/mopidy.conf'
logger = setup_logger("Mopidy Controller")
decay = np.zeros(GPIO_LEN, dtype='float32')

if os.path.exists(FIFO_PATH):
    os.remove(FIFO_PATH)
os.mkfifo(FIFO_PATH, 0o0777)

fft_calc = fft.FFT(CHUNK_SIZE,
                   SAMPLE_RATE,
                   GPIO_LEN,
                   MIN_FREQUENCY,
                   MAX_FREQUENCY,
                   CUSTOM_CHANNEL_MAPPING,
                   CUSTOM_CHANNEL_FREQUENCIES,
                   1)


class LightShowService(services.Service.Service):

    def __init__(self):
        super().__init__()
        self.requires_gpio = True
        self.process = None

    def run(self):
        self.process = subprocess.Popen(['mopidy', '--config', config_path],
                                        stdout=subprocess.PIPE,
                                        stdin=subprocess.PIPE,
                                        preexec_fn=os.setsid)

        chunks_per_sec = ((16 * INPUT_CHANNELS * SAMPLE_RATE) / 8) / CHUNK_SIZE
        light_delay = int(DELAY * chunks_per_sec)
        matrix_buffer = deque([], 1000)

        mean = np.array([12.0 for _ in range(GPIO_LEN)], dtype='float32')
        std = np.array([1.5 for _ in range(GPIO_LEN)], dtype='float32')

        running_stats = RunningStats.Stats(GPIO_LEN)
        running_stats.preload(mean, std, GPIO_LEN)

        file = os.open(FIFO_PATH, os.O_RDONLY | os.O_NONBLOCK)

        while True:

            try:
                data = os.read(file, CHUNK_SIZE)

            except OSError as err:
                if err.errno == errno.EAGAIN or err.errno == errno.EWOULDBLOCK:
                    continue

            if len(data):
                # if the maximum of the absolute value of all samples in
                # data is below a threshold we will disregard it
                audio_max = audioop.max(data, 2)
                if audio_max < 250:
                    # we will fill the matrix with zeros and turn the lights off
                    matrix = np.zeros(GPIO_LEN, dtype="float32")
                    logger.debug("below threshold: '" + str(audio_max) + "', turning the lights off")
                else:
                    matrix = fft_calc.calculate_levels(data)
                    running_stats.push(matrix)
                    mean = running_stats.mean()
                    std = running_stats.std()

                matrix_buffer.appendleft(matrix)

                if len(matrix_buffer) > light_delay:
                    matrix = matrix_buffer[light_delay]
                    update_lights(matrix, mean, std)

            self.mutex.acquire()
            if self.should_stop:
                break
            self.mutex.release()
        self.process.terminate()
        os.unlink(FIFO_PATH)
        hardware_adapter.disable_gpio()


def update_lights(matrix, mean, std):
    """Update the state of all the lights

    Update the state of all the lights based upon the current
    frequency response matrix

    :param matrix: row of data from cache matrix
    :type matrix: list

    :param mean: standard mean of fft values
    :type mean: list

    :param std: standard deviation of fft values
    :type std: list
    """
    global decay

    brightness = matrix - mean + (std * SD_LOW)
    brightness = (brightness / (std * (SD_LOW + SD_HIGH))) * \
                 (1.0 - (ATTENUATE_PCT / 100.0))

    # insure that the brightness levels are in the correct range
    brightness = np.clip(brightness, 0.0, 1.0)
    brightness = np.round(brightness, decimals=3)

    # calculate light decay rate if used
    if DECAY_FACTOR > 0:
        decay = np.where(decay <= brightness, brightness, decay)
        brightness = np.where(decay - DECAY_FACTOR > 0, decay - DECAY_FACTOR, brightness)
        decay = np.where(decay - DECAY_FACTOR > 0, decay - DECAY_FACTOR, decay)

    for blevel, pin in zip(brightness, range(GPIO_LEN)):
            hardware_adapter.set_pin_level(pin, blevel)

