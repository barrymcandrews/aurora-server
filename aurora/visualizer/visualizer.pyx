from collections import deque
import audioop
from typing import List
import numpy as np
cimport numpy as np
from aurora import hardware
from aurora.configuration import Channel, Configuration
from fft cimport FFT
from running_stats cimport Stats

cm = Configuration()

cdef class Visualizer(object):

    cdef np.float32_t[:] decay, mean, std
    cdef Stats running_stats
    cdef FFT fft_calc
    cdef object filter, matrix_buffer
    cdef list channels
    cdef int num_channels, light_delay

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
        self.running_stats.preload(np.asarray(self.mean), np.asarray(self.std), self.num_channels)

    cpdef visualize(self, bytes data):
        if len(data):
            # if the maximum of the absolute value of all samples in
            # data is below a threshold we will disregard it
            audio_max = audioop.max(data, 2)
            if audio_max < 250:
                # we will fill the matrix with zeros and turn the lights off
                matrix = np.zeros(self.num_channels, dtype=np.float32)
                # log.debug("below threshold: '" + str(audio_max) + "', turning the lights off")
            else:
                matrix = self.fft_calc.calculate_levels(data)
                self.running_stats.push(matrix)
                self.mean = self.running_stats.mean()
                self.std = self.running_stats.std()

            self.matrix_buffer.appendleft(matrix)

            if len(self.matrix_buffer) > self.light_delay:
                matrix = self.matrix_buffer[self.light_delay]

                self.update_lights(np.asarray(matrix), np.asarray(self.mean), np.asarray(self.std))

    cdef update_lights(self, np.ndarray[np.float32_t, ndim=1] matrix,
                             np.ndarray[np.float32_t, ndim=1] mean,
                             np.ndarray[np.float32_t, ndim=1] std):

        cdef np.ndarray[np.float32_t, ndim=1] brightness
        cdef np.ndarray[np.float32_t, ndim=1] decay
        cdef int decay_factor

        brightness = matrix - mean + (std * self.filter.sd_low)
        brightness = (brightness / (std * (self.filter.sd_low + self.filter.sd_high))) * \
                     (1.0 - (self.filter.attenuate_pct / 100.0))

        # insure that the brightness levels are in the correct range
        brightness = np.clip(brightness, 0.0, 1.0)
        brightness = np.round(brightness, decimals=3)

        # calculate light decay rate if used
        decay_factor = self.filter.decay_factor
        if decay_factor > 0:
            decay = np.asarray(self.decay)
            decay = np.where(decay <= brightness, brightness, decay)
            brightness = np.where(decay - decay_factor > 0, decay - decay_factor, brightness)
            decay = np.where(decay - decay_factor > 0, decay - decay_factor, decay)
            self.decay = decay

        for level, c_index in zip(brightness, range(self.num_channels)):
            hardware.set_pwm(self.channels[c_index].pin, int(level * 100))
