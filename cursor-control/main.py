import time

from brainflow import DataFilter, DetrendOperations, WindowFunctions

import board_reader
import expirement_gui.one_dim_control as one_dim
import expirement_gui.tk_plots as tk_plots

channels = {"o1": 1, "c3": 2, "fp2": 3, "fp1": 4, "c4": 5, "cz": 6, "fz": 7, "o2": 8}


def main():
    one_dim_experiment = one_dim.OneDimensionControlExperiment()
    tk_plots.BandPowerChart(
        one_dim_experiment.plots_canvas, 0, 1, ["delta", "theta", "alpha", "beta"]
    )
    board = board_reader.BoardReader()  # defaults to Cyton
    with board:
        samp_rate = board.get_sampling_rate()
        nfft = DataFilter.get_nearest_power_of_two(samp_rate)
        for _ in range(0, 10):
            time.sleep(2)
            data = board.pop_board_data()
            c3_cz = data[channels["c3"]] - data[channels["cz"]]
            DataFilter.detrend(c3_cz, DetrendOperations.LINEAR.value)
            psd = DataFilter.get_psd_welch(
                c3_cz,
                nfft,
                nfft // 2,
                samp_rate,
                WindowFunctions.BLACKMAN_HARRIS.value,
            )
            band_power_alpha = DataFilter.get_band_power(psd, 10, 12)
            print(band_power_alpha)


# TODO: hook alpha band power into experimental gui based on average before experiment start
# TODO: add a count down before experiment start
# TODO: write data collected during experiment to disk for later analysis


if __name__ == "__main__":
    main()
