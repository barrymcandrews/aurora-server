from collections import deque
import audioop
from logging import Logger
import numpy
import alsaaudio as aa

import time
from numpy import ndarray
from aurora_server.lights.fft import FFT
from aurora_server import configuration
from aurora_server.lights.running_stats import Stats
from aurora_server.lights.pins import Device
from aurora_server.log import setup_logger

cm = configuration.Configuration()
log = setup_logger("Audio Filter")


class Visualizer(object):

    def __init__(self, device: Device):
        super().__init__()
        self.updates = 0
        self.start_time = time.time()
        self.device = device
        self.num_channels = len(device.pins)
        self.decay = numpy.zeros(self.num_channels, dtype='float32')
        self.fft_calc = FFT(cm.lights.chunk_size,
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

        self.mean = numpy.array([12.0 for _ in range(self.num_channels)], dtype='float32')
        self.std = numpy.array([1.5 for _ in range(self.num_channels)], dtype='float32')

        self.running_stats = Stats(self.num_channels)
        self.running_stats.preload(self.mean, self.std, self.num_channels)

        # Audio Output

        self.output_device = aa.PCM(aa.PCM_PLAYBACK, aa.PCM_NORMAL, 'default')
        self.output_device.setchannels(self.num_channels)
        self.output_device.setrate(cm.lights.sample_rate)
        self.output_device.setformat(aa.PCM_FORMAT_S16_LE)
        self.output_device.setperiodsize(cm.lights.chunk_size)

    def __del__(self):
        end_time = time.time()
        print("Updates/Second: " + str(self.updates/(end_time - self.start_time)))

    def visualize_and_play(self, data: bytes):
        self.visualize(data)
        try:
            self.output_device.write(data)
        except aa.ALSAAudioError:
            log.error("ALSA Audio Exception!")

    def visualize(self, data: bytes):
        if self.updates == 0:
            self.start_time = time.time()
        if len(data):
            # if the maximum of the absolute value of all samples in
            # data is below a threshold we will disregard it
            audio_max = audioop.max(data, 2)
            if audio_max < 250:
                # we will fill the matrix with zeros and turn the lights off
                matrix = numpy.zeros(self.num_channels, dtype="float32")
                log.debug("below threshold: '" + str(audio_max) + "', turning the lights off")
            else:
                matrix = self.fft_calc.calculate_levels(data)
                self.running_stats.push(matrix)
                self.mean = self.running_stats.mean()
                self.std = self.running_stats.std()

            self.matrix_buffer.appendleft(matrix)

            if len(self.matrix_buffer) > self.light_delay:
                matrix = self.matrix_buffer[self.light_delay]
                self.update_lights(matrix, self.mean, self.std)

    def update_lights(self, matrix: ndarray, mean: ndarray, std: ndarray):
        brightness = matrix - mean + (std * cm.lights.SD_low)
        brightness = (brightness / (std * (cm.lights.SD_low + cm.lights.SD_high))) * \
                     (1.0 - (cm.lights.attenuate_pct / 100.0))

        # insure that the brightness levels are in the correct range
        brightness = numpy.clip(brightness, 0.0, 1.0)
        brightness = numpy.round(brightness, decimals=3)

        # calculate light decay rate if used
        decay_factor = cm.lights.decay_factor
        if decay_factor > 0:
            self.decay = numpy.where(self.decay <= brightness, brightness, self.decay)
            brightness = numpy.where(self.decay - decay_factor > 0, self.decay - decay_factor, brightness)
            self.decay = numpy.where(self.decay - decay_factor > 0, self.decay - decay_factor, self.decay)

        self.updates = self.updates + 1
        log.info("Visualizing: " + str(brightness))
        for level, p_index in zip(brightness, range(self.num_channels)):
                self.device.set_pin_at_index(p_index, int(level * 100))
