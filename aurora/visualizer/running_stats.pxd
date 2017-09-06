cimport numpy as np


cdef class Stats(object):
    cdef:
        public int length, sample_count
        public np.float32_t[:] empty, old_mean, old_std, new_mean, new_std

    cdef clear(self)

    cdef public void preload(self, np.ndarray[np.float32_t, ndim=1] mean, np.ndarray[np.float32_t, ndim=1] std, int sample_count)

    cdef public void push(self, np.ndarray[np.float32_t, ndim=1] data)

    cdef public int num_data_values(self)

    cdef public np.ndarray[np.float32_t, ndim=1] mean(self)

    cdef public np.ndarray[np.float32_t, ndim=1] variance(self)

    cdef public np.ndarray[np.float32_t, ndim=1] std(self)
