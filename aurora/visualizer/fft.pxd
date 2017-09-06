cimport numpy as np

cdef class FFT(object):
    cdef:
        public int chunk_size, sample_rate, num_bins, min_frequency, max_frequency, input_channels
        public np.float32_t[:] window
        public list frequency_limits, piff
        public object custom_channel_mapping, custom_channel_frequencies, audio_levels

    cdef public np.ndarray[np.float32_t, ndim=1] calculate_levels(self, bytes data_frames)

    cdef public list calculate_channel_frequency(self)
