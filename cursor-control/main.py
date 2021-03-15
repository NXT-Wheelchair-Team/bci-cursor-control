import time

from brainflow import DataFilter, DetrendOperations, WindowFunctions

import board_reader
import expirement_gui.one_dim_control as one_dim
import expirement_gui.tk_plots as tk_plots

channels = {"o1": 1, "c3": 2, "fp2": 3, "fp1": 4, "c4": 5, "cz": 6, "fz": 7, "o2": 8}
POWER_BAND_LOW = 10
POWER_BAND_HIGH = 12
WINDOW_SIZE_SAMPLES = 256  # must be a power of two
PRE_EXPERIMENT_AVG_TIME_S = 5
SAMP_RATE = 250


def pre_experiment(board: board_reader.BoardReader, band_power_chart) -> float:
    """
    :return: average band power for pre-experiment phase
    """
    time.sleep(PRE_EXPERIMENT_AVG_TIME_S)
    data = board.get_board_data(PRE_EXPERIMENT_AVG_TIME_S * SAMP_RATE)
    c3 = data[channels["c3"]]
    DataFilter.detrend(c3, DetrendOperations.LINEAR.value)
    psd = DataFilter.get_psd_welch(
        c3,
        1024,
        1024 // 2,
        SAMP_RATE,
        WindowFunctions.BLACKMAN_HARRIS.value,
    )
    band_power_alpha = DataFilter.get_band_power(psd, 10, 12)
    band_power_chart.bar([band_power_alpha])
    return band_power_alpha


def single_run_experiment(
    board: board_reader.BoardReader,
    band_power_chart: tk_plots.BandPowerChart,
    one_dim_experiment: one_dim.OneDimensionControlExperiment,
    band_power_avg: float,
):
    time_start = time.time()
    while time.time() - time_start < 10:
        time.sleep(0.1)
        data = board.get_board_data(SAMP_RATE * 2)
        c3 = data[channels["c3"]]
        DataFilter.detrend(c3, DetrendOperations.LINEAR.value)
        psd = DataFilter.get_psd_welch(
            c3,
            WINDOW_SIZE_SAMPLES,
            WINDOW_SIZE_SAMPLES // 2,
            SAMP_RATE,
            WindowFunctions.BLACKMAN_HARRIS.value,
        )
        band_power_alpha = DataFilter.get_band_power(psd, 10, 12)
        print(
            f"Band power 10-12Hz for last {(WINDOW_SIZE_SAMPLES // SAMP_RATE)} seconds: {band_power_alpha} - compared against average {band_power_avg}"
        )
        band_power_chart.bar([band_power_alpha])
        if band_power_alpha > band_power_avg:
            one_dim_experiment.cursor.set_velocity(5)
        else:
            one_dim_experiment.cursor.set_velocity(-5)
    one_dim_experiment.reset()


def main():
    one_dim_experiment = one_dim.OneDimensionControlExperiment()
    band_power_chart = tk_plots.BandPowerChart(
        one_dim_experiment.plots_canvas, 0, 5, ["10-12 Hz"]
    )
    board = board_reader.BoardReader()  # defaults to Cyton
    with board:
        average = pre_experiment(board, band_power_chart)
        print(f"Average band power 10-12Hz = {average}")
        for _ in range(0, 10):
            single_run_experiment(board, band_power_chart, one_dim_experiment, average)


# TODO: hook alpha band power into experimental gui based on average before experiment start
# TODO: add a count down before experiment start
# TODO: write data collected during experiment to disk for later analysis


if __name__ == "__main__":
    main()
