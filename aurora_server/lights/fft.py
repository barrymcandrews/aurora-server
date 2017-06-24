#
# Licensed under the BSD license.  See full license in LICENSE file.
# http://www.lightshowpi.com/
#
# Author: Todd Giles (todd@lightshowpi.com)
# Author: Tom Enos (tomslick.ca@gmail.com)

"""FFT methods for computing / analyzing frequency response of audio.

This is simply a wrapper around rpi-audio-level by Colin Guyon.
https://github.com/colin-guyon/rpi-audio-levels

Initial FFT code inspired from the code posted here:
http://www.raspberrypi.org/phpBB3/viewtopic.php?t=35838&p=454041

Optimizations from work by Scott Driscoll:
http://www.instructables.com/id/Raspberry-Pi-Spectrum-Analyzer-with-RGB-LED-Strip-/

Third party dependencies:

numpy: for array support - http://www.numpy.org/
rpi-audio-levels - https://bitbucket.org/tom_slick/rpi-audio-levels (modified for lightshowpi)
"""

import math
from rpi_audio_levels import AudioLevels

from numpy import *

from aurora_server.log import setup_logger

logging = setup_logger('FFT')


class FFT(object):
    def __init__(self,
                 chunk_size,
                 sample_rate,
                 num_bins,
                 min_frequency,
                 max_frequency,
                 custom_channel_mapping,
                 custom_channel_frequencies,
                 input_channels=2):
        """
        :param chunk_size: chunk size of audio data
        :type chunk_size: int

        :param sample_rate: audio file sample rate
        :type sample_rate: int

        :param num_bins: length of gpio to process
        :type num_bins: int

        :param input_channels: number of audio input channels to process for (default=2)
        :type input_channels: int

        :param min_frequency: lowest frequency for which a channel will be activated
        :type min_frequency: float

        :param max_frequency: max frequency for which a channel will be activated.
        :type max_frequency: float

        :param custom_channel_mapping: custom map of channels to different frequencies
        :type custom_channel_mapping: list | int

        :param custom_channel_frequencies: custom list of frequencies that should be
                                        utilized for each channel
        :type custom_channel_frequencies: list | int

        """

        self.chunk_size = chunk_size
        self.sample_rate = sample_rate
        self.num_bins = num_bins
        self.input_channels = input_channels
        self.window = hanning(0)
        self.min_frequency = min_frequency
        self.max_frequency = max_frequency
        self.custom_channel_mapping = custom_channel_mapping
        self.custom_channel_frequencies = custom_channel_frequencies
        self.frequency_limits = self.calculate_channel_frequency()
        self.config_filename = ""
        self.audio_levels = AudioLevels(math.log(chunk_size / 2, 2), num_bins)

        fl = array(self.frequency_limits)
        self.piff = ((fl * self.chunk_size) / self.sample_rate).astype(int)

        for a in range(len(self.piff)):
            if self.piff[a][0] == self.piff[a][1]:
                self.piff[a][1] += 1
        self.piff = self.piff.tolist()

    def calculate_levels(self, data):
        """Calculate frequency response for each channel defined in frequency_limits

        :param data: decoder.frames(), audio data for fft calculations
        :type data: decoder.frames

        :return:
        :rtype: numpy.array
        """
        # create a numpy array, taking just the left channel if stereo
        data_stereo = frombuffer(data, dtype="int16")

        if self.input_channels == 2:
            # data has 2 bytes per channel
            # pull out the even values, just using left channel
            data = array(data_stereo[::2])
        elif self.input_channels == 1:
            data = data_stereo

        # if you take an FFT of a chunk of audio, the edges will look like
        # super high frequency cutoffs. Applying a window tapers the edges
        # of each end of the chunk down to zero.
        if len(data) != len(self.window):
            self.window = hanning(len(data)).astype(float32)

        data = data * self.window

        # if all zeros in data then there is no need to do the fft
        if all(data == 0.0):
            return zeros(self.num_bins, dtype="float32")

        # Apply FFT - real data
        # Calculate the power spectrum
        cache_matrix = array(self.audio_levels.compute(data, self.piff)[0])
        cache_matrix[isinf(cache_matrix)] = 0.0

        return cache_matrix

    def calculate_channel_frequency(self):
        """Calculate frequency values

        Calculate frequency values for each channel,
        taking into account custom settings.

        :return: frequency values for each channel
        :rtype: list
        """

        # How many channels do we need to calculate the frequency for
        if self.custom_channel_mapping != 0 and len(self.custom_channel_mapping) == self.num_bins:
            logging.debug("Custom Channel Mapping is being used: %s",
                          str(self.custom_channel_mapping))
            channel_length = max(self.custom_channel_mapping)
        else:
            logging.debug("Normal Channel Mapping is being used.")
            channel_length = self.num_bins

        logging.debug("Calculating frequencies for %d channels.", channel_length)
        octaves = (log(self.max_frequency / self.min_frequency)) / log(2)
        logging.debug("octaves in selected frequency range ... %s", octaves)
        octaves_per_channel = octaves / channel_length
        frequency_limits = []
        frequency_store = []

        frequency_limits.append(self.min_frequency)

        if self.custom_channel_frequencies != 0 and (
                    len(self.custom_channel_frequencies) >= channel_length + 1):
            logging.debug("Custom channel frequencies are being used")
            frequency_limits = self.custom_channel_frequencies
        else:
            logging.debug("Custom channel frequencies are not being used")
            for pin in range(1, self.num_bins + 1):
                frequency_limits.append(frequency_limits[-1]
                                        * 10 ** (3 / (10 * (1 / octaves_per_channel))))
        for pin in range(0, channel_length):
            frequency_store.append((frequency_limits[pin], frequency_limits[pin + 1]))
            logging.debug("channel %d is %6.2f to %6.2f ", pin, frequency_limits[pin],
                          frequency_limits[pin + 1])

        # we have the frequencies now lets map them if custom mapping is defined
        if self.custom_channel_mapping != 0 and len(self.custom_channel_mapping) == self.num_bins:
            frequency_map = []

            for pin in range(0, self.num_bins):
                mapped_channel = self.custom_channel_mapping[pin] - 1
                mapped_frequency_set = frequency_store[mapped_channel]
                mapped_frequency_set_low = mapped_frequency_set[0]
                mapped_frequency_set_high = mapped_frequency_set[1]
                logging.debug("mapped channel: " + str(mapped_channel) + " will hold LOW: "
                              + str(mapped_frequency_set_low) + " HIGH: "
                              + str(mapped_frequency_set_high))
                frequency_map.append(mapped_frequency_set)

            return frequency_map
        else:
            return frequency_store
