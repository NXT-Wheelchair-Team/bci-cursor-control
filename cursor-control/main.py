import time

from brainflow import DataFilter, DetrendOperations, WindowFunctions

import board_reader
import expirement_gui.one_dim_control as one_dim


def main():
    board = board_reader.BoardReader()  # defaults to Cyton
    with board:
        eeg_channels = board.get_eeg_channels()
        c4_eeg = eeg_channels[5]
        samp_rate = board.get_sampling_rate()
        nfft = DataFilter.get_nearest_power_of_two(samp_rate)
        for _ in range(0, 10):
            time.sleep(2)
            data = board.pop_board_data()
            DataFilter.detrend(data[c4_eeg], DetrendOperations.LINEAR.value)
            psd = DataFilter.get_psd_welch(
                data[c4_eeg],
                nfft,
                nfft // 2,
                samp_rate,
                WindowFunctions.BLACKMAN_HARRIS.value,
            )
            band_power_alpha = DataFilter.get_band_power(psd, 7.0, 13.0)
            print(band_power_alpha)


# TODO: FFT & band power display next to the experiment window
# TODO: hook alpha band power into experimental gui based on average before experiment start
# TODO: add a count down before experiment start
# TODO: write data collected during experiment to disk for later analysis


if __name__ == "__main__":
    main()
