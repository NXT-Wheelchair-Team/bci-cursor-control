from typing import Tuple, Union

import brainflow as bf
import numpy as np


class PSDPreProcessor:
    def __init__(self, sample_rate: int, window_size: int = 512, overlap_percentage: float = .5,
                 window_func: bf.WindowFunctions = bf.WindowFunctions.BLACKMAN_HARRIS,
                 detrend_operation: bf.DetrendOperations = bf.DetrendOperations.LINEAR):
        """
        Calculate PSD of the provided data by the Welch method.

        :param sample_rate: sample rate of the board
        :param window_size: number of samples per window, must be power of two
        :param overlap_percentage: overlap between windows, 0.0 through 0.99
        :param window_func: windowing function to use in PSD calculation"""
        self.sample_rate = sample_rate
        self.window_size = window_size
        self.overlap_percentage = overlap_percentage
        self.overlap_samples = int(self.window_size * self.overlap_percentage)
        self.window_func = window_func
        self.detrend_operation = detrend_operation
        self.data: Union[bf.NDArray[bf.Float64], None] = None
        self.psd: Union[Tuple[bf.NDArray[bf.Float64], bf.NDArray[bf.Float64]], None] = None  # amplitude, frequency pair

    def process_data(self, data: bf.NDArray[bf.Float64]):
        """
        Process new set of sampled data. Length of data should be larger than the window size.

        :param data: array of data to process, a copy will be made internally
        """
        self.data = np.copy(data)

        bf.DataFilter.detrend(self.data, self.detrend_operation)

    def _process_psd(self, data: bf.NDArray[bf.Float64]) -> Tuple[
        bf.NDArray[bf.Float64], bf.NDArray[bf.Float64]]:
        """
        Calculate PSD of the provided data by the Welch method.

        :param data: array of Float64 values
        :return: tuple of amplitudes and corresponding frequencies in form of numpy arrays with Float64 types
        """
        overlap_samples = int(self.window_size * self.overlap_percentage)
        return bf.DataFilter.get_psd_welch(
            data,
            self.window_size,
            overlap_samples,
            self.sample_rate,
            self.window_func
        )


def get_band_power_from_psd
