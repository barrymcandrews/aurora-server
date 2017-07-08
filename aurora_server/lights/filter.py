import audioop
from collections import deque
from multiprocessing import Queue

import numpy as np

import aurora_server.lights.fft as fft
from aurora_server import configuration, fifo
from aurora_server.audio import fifo
from aurora_server.lights import running_stats
from aurora_server.log import setup_logger

cm = configuration.Configuration()
logger = setup_logger("Audio Filter")


class Filter(object):

    def __init__(self, device):
        super().__init__()
        self.device = device
        self.num_channels = len(device.pins)
        self.decay = np.zeros(self.num_channels, dtype='float32')
        self.fft_calc = fft.FFT(cm.lights.chunk_size,
                                cm.lights.sample_rate,
                                self.num_channels,
                                cm.lights.min_frequency,
                                cm.lights.max_frequency,
                                cm.lights.custom_channel_mapping,
                                cm.lights.custom_channel_frequencies,
                                1)

        chunks_per_sec = ((16 * cm.lights.input_channels * cm.lights.sample_rate) / 8) \
            / cm.lights.chunk_size
        self.light_delay = int(cm.lights.delay * chunks_per_sec)
        self.matrix_buffer = deque([], 1000)

        self.mean = np.array([12.0 for _ in range(self.num_channels)], dtype='float32')
        self.std = np.array([1.5 for _ in range(self.num_channels)], dtype='float32')

        self.running_stats = running_stats.Stats(self.num_channels)
        self.running_stats.preload(self.mean, self.std, self.num_channels)

    def process_audio(self):
            input_q = Queue()
            fifo.start_reading(input_q)

            while True:
                data = input_q.get(block=False)

                if len(data):
                    # if the maximum of the absolute value of all samples in
                    # data is below a threshold we will disregard it
                    audio_max = audioop.max(data, 2)
                    if audio_max < 250:
                        # we will fill the matrix with zeros and turn the lights off
                        matrix = np.zeros(self.num_channels, dtype="float32")
                        logger.debug("below threshold: '" + str(audio_max) + "', turning the lights off")
                    else:
                        matrix = self.fft_calc.calculate_levels(data)
                        self.running_stats.push(matrix)
                        self.mean = self.running_stats.mean()
                        self.std = self.running_stats.std()
                        self.matrix_buffer.appendleft(matrix)

                    if len(self.matrix_buffer) > self.light_delay:
                        matrix = self.matrix_buffer[self.light_delay]
                        self.update_lights(matrix, self.mean, self.std)

    def update_lights(self, matrix, mean, std):
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

        brightness = matrix - mean + (std * cm.lights.SD_low)
        brightness = (brightness / (std * (cm.lights.SD_low + cm.lights.SD_high))) * \
                     (1.0 - (cm.lights.attenuate_pct / 100.0))

        # insure that the brightness levels are in the correct range
        brightness = np.clip(brightness, 0.0, 1.0)
        brightness = np.round(brightness, decimals=3)

        # calculate light decay rate if used
        decay_factor = cm.lights.decay_factor
        if decay_factor > 0:
            self.decay = np.where(self.decay <= brightness, brightness, self.decay)
            brightness = np.where(self.decay - decay_factor > 0, self.decay - decay_factor, brightness)
            self.decay = np.where(self.decay - decay_factor > 0, self.decay - decay_factor, self.decay)

        for level, pin in zip(brightness, range(self.num_channels)):
                self.device.set_pin_level(pin, level)

