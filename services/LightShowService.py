import subprocess
import signal
import audioop
import os
import numpy as np
import errno
import RunningStats
from collections import deque

import fft
import hardware_adapter
import services.Service
import configuration_manager
from log import setup_logger

cm = configuration_manager.Configuration()

GPIO_LEN = 3

config_path = os.path.dirname(os.path.realpath(__file__)) + '/../config/mopidy.conf'
logger = setup_logger("Light Show Service")
decay = np.zeros(GPIO_LEN, dtype='float32')
fft_calc = fft.FFT(cm.light_show.chunk_size,
                   cm.light_show.sample_rate,
                   GPIO_LEN,
                   cm.light_show.min_frequency,
                   cm.light_show.max_frequency,
                   cm.light_show.custom_channel_mapping,
                   cm.light_show.custom_channel_frequencies,
                   1)


class LightShowService(services.Service.Service):

    def __init__(self):
        super().__init__()
        self.requires_gpio = True
        self.process = None

    def run(self):
        hardware_adapter.enable_gpio()
        setup_fifo()
        self.process = subprocess.Popen(['mopidy', '--config', config_path],
                                        stdout=subprocess.PIPE,
                                        stdin=subprocess.PIPE,
                                        preexec_fn=os.setsid)

        chunks_per_sec = ((16 * cm.light_show.input_channels * cm.light_show.sample_rate) / 8) \
            / cm.light_show.chunk_size
        light_delay = int(cm.light_show.delay * chunks_per_sec)
        matrix_buffer = deque([], 1000)

        mean = np.array([12.0 for _ in range(GPIO_LEN)], dtype='float32')
        std = np.array([1.5 for _ in range(GPIO_LEN)], dtype='float32')

        running_stats = RunningStats.Stats(GPIO_LEN)
        running_stats.preload(mean, std, GPIO_LEN)

        file = os.open(cm.light_show.fifo_path, os.O_RDONLY | os.O_NONBLOCK)

        while True:
            try:
                data = os.read(file, cm.light_show.chunk_size)

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

        os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
        self.process.wait()
        os.unlink(cm.light_show.fifo_path)
        hardware_adapter.disable_gpio()


def setup_fifo():
    if os.path.exists(cm.light_show.fifo_path):
        os.remove(cm.light_show.fifo_path)
    os.mkfifo(cm.light_show.fifo_path, 0o0777)


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

    brightness = matrix - mean + (std * cm.light_show.SD_low)
    brightness = (brightness / (std * (cm.light_show.SD_low + cm.light_show.SD_high))) * \
                 (1.0 - (cm.light_show.attenuate_pct / 100.0))

    # insure that the brightness levels are in the correct range
    brightness = np.clip(brightness, 0.0, 1.0)
    brightness = np.round(brightness, decimals=3)

    # calculate light decay rate if used
    decay_factor = cm.light_show.decay_factor
    if decay_factor > 0:
        decay = np.where(decay <= brightness, brightness, decay)
        brightness = np.where(decay - decay_factor > 0, decay - decay_factor, brightness)
        decay = np.where(decay - decay_factor > 0, decay - decay_factor, decay)

    for blevel, pin in zip(brightness, range(GPIO_LEN)):
            hardware_adapter.set_pin_level(pin, blevel)

