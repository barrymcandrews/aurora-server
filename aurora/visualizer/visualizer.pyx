from collections import deque
import audioop
from typing import List
import numpy as np
cimport numpy as np
from aurora import hardware
from aurora.configuration import Channel, Configuration
from aurora.visualizer.fft import FFT
from aurora.visualizer.running_stats import Stats

cm = Configuration()

cdef class Visualizer(object):

    def __init__(self, channels: List[Channel], vfilter: Configuration.Filter):
        super().__init__()
        self.filter = vfilter
        self.channels = channels
        self.num_channels = len(self.channels)
        self.decay = np.zeros(self.num_channels, dtype=np.float32)
        self.fft_calc = FFT(self.filter.chunk_size,
                            self.filter.sample_rate,
                            self.num_channels,
                            self.filter.min_frequency,
                            self.filter.max_frequency,
                            self.filter.custom_channel_mapping,
                            self.filter.custom_channel_frequencies,
                            1)

        chunks_per_sec = ((16 * self.filter.input_channels * self.filter.sample_rate) / 8) \
                         / self.filter.chunk_size
        self.light_delay = int(self.filter.delay * chunks_per_sec)
        self.matrix_buffer = deque([], 1000)

        self.mean = np.array([12.0 for _ in range(self.num_channels)], dtype=np.float32)
        self.std = np.array([1.5 for _ in range(self.num_channels)], dtype=np.float32)

        self.running_stats = Stats(self.num_channels)
        self.running_stats.preload(self.mean, self.std, self.num_channels)

    cpdef visualize(self, data):
        if len(data):
            # if the maximum of the absolute value of all samples in
            # data is below a threshold we will disregard it
            audio_max = audioop.max(data, 2)
            if audio_max < 250:
                # we will fill the matrix with zeros and turn the lights off
                matrix = np.zeros(self.num_channels, dtype=np.float64)
                # log.debug("below threshold: '" + str(audio_max) + "', turning the lights off")
            else:
                matrix = self.fft_calc.calculate_levels(data)
                self.running_stats.push(matrix)
                self.mean = self.running_stats.mean()
                self.std = self.running_stats.std()

            self.matrix_buffer.appendleft(matrix)

            if len(self.matrix_buffer) > self.light_delay:
                matrix = self.matrix_buffer[self.light_delay]
                self.update_lights(matrix, self.mean, self.std)

    cdef update_lights(self, matrix, mean, std):

        brightness = matrix - mean + (std * self.filter.sd_low)
        brightness = (brightness / (std * (self.filter.sd_low + self.filter.sd_high))) * \
                     (1.0 - (self.filter.attenuate_pct / 100.0))

        # insure that the brightness levels are in the correct range
        brightness = np.clip(brightness, 0.0, 1.0)
        brightness = np.round(brightness, decimals=3)

        # calculate light decay rate if used
        decay_factor = self.filter.decay_factor
        if decay_factor > 0:
            self.decay = np.where(self.decay <= brightness, brightness, self.decay)
            brightness = np.where(self.decay - decay_factor > 0, self.decay - decay_factor, brightness)
            self.decay = np.where(self.decay - decay_factor > 0, self.decay - decay_factor, self.decay)

        for level, c_index in zip(brightness, range(self.num_channels)):
            hardware.set_pwm(self.channels[c_index].pin, int(level * 100))
