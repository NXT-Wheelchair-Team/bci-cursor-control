import time

import board_reader
import expirement_gui.one_dim_control as one_dim
import expirement_gui.tk_plots as tk_plots
import feature_extraction

channels = {"o1": 1, "c3": 2, "fp2": 3, "fp1": 4, "c4": 5, "cz": 6, "fz": 7, "o2": 8}
POWER_BAND_LOW = 10
POWER_BAND_HIGH = 12
WINDOW_SIZE_SAMPLES = 256  # must be a power of two
PRE_EXPERIMENT_AVG_TIME_S = 5
SAMP_RATE = 250
BAND_FEATURE_LOW_FREQ = 10
BAND_FEATURE_HIGH_FREQ = 12
TRIAL_LENGTH_S = 20


def get_psd_feature(
    board: board_reader.BoardReader,
    psd_extractor: feature_extraction.PSDFeatureExtractor,
    data_len_s: float,
    channel_id: str = "c3",
):
    data = board.get_board_data(int(data_len_s * board.get_sampling_rate()))
    c3 = data[channels[channel_id]]
    psd_extractor.process_data(c3)
    return psd_extractor.get_band_power(BAND_FEATURE_LOW_FREQ, BAND_FEATURE_HIGH_FREQ)


def chart_bands(
    primary_feature,
    psd_extractor: feature_extraction.PSDFeatureExtractor,
    band_power_chart: tk_plots.BandPowerChart,
):
    standard_bands = [(0.5, 4), (4, 7), (8, 15), (16, 31)]
    values = [primary_feature]  # start with our primary feature and append others on
    for band in standard_bands:
        start_freq, end_freq = band
        values.append(psd_extractor.get_band_power(start_freq, end_freq))
    band_power_chart.bar(values)


def pre_experiment(
    board: board_reader.BoardReader,
    psd_extractor: feature_extraction.PSDFeatureExtractor,
    band_power_chart,
) -> float:
    """
    :return: average band power for pre-experiment phase
    """
    print(
        f"Taking PSD baseline before start, will take {PRE_EXPERIMENT_AVG_TIME_S} seconds"
    )
    time.sleep(PRE_EXPERIMENT_AVG_TIME_S)  # let the board reader collect data
    band_power_feature = get_psd_feature(
        board, psd_extractor, PRE_EXPERIMENT_AVG_TIME_S
    )
    chart_bands(band_power_feature, psd_extractor, band_power_chart)
    return band_power_feature


def run_single_trial(
    board: board_reader.BoardReader,
    psd_extractor: feature_extraction.PSDFeatureExtractor,
    band_power_chart: tk_plots.BandPowerChart,
    one_dim_experiment: one_dim.OneDimensionControlExperiment,
    band_power_avg: float,
):
    print("Starting experiment")
    time_start = time.time()
    while (
        time.time() - time_start < TRIAL_LENGTH_S
        and not one_dim_experiment.target_reached
    ):
        time.sleep(0.1)  # let another tenth of a second worth of data accrue
        band_power_feature = get_psd_feature(board, psd_extractor, data_len_s=3)
        print(
            f"Band power 10-12Hz for last {(WINDOW_SIZE_SAMPLES // SAMP_RATE)} seconds: {band_power_feature} - compared against average {band_power_avg}"
        )
        chart_bands(band_power_feature, psd_extractor, band_power_chart)
        if band_power_feature > band_power_avg:
            one_dim_experiment.cursor.set_velocity(50)
        else:
            one_dim_experiment.cursor.set_velocity(-50)
        one_dim_experiment.update()

    print(f"Target reached: {one_dim_experiment.target_reached}")
    if not one_dim_experiment.target_reached:
        one_dim_experiment.notify_target_not_reached()
        one_dim_experiment.update()

    one_dim_experiment.cursor.set_velocity(0)


def main():
    one_dim_experiment = one_dim.OneDimensionControlExperiment()
    band_power_chart = tk_plots.BandPowerChart(
        one_dim_experiment.plots_canvas,
        y_min=0,
        y_max=10,
        band_labels=[
            f"{BAND_FEATURE_LOW_FREQ}-{BAND_FEATURE_HIGH_FREQ} Hz",
            "Delta",
            "Theta",
            "Alpha",
            "Beta",
        ],
    )
    board = board_reader.BoardReader()  # defaults to Cyton
    board_reader.FileWriter(board)
    psd_feature_extractor = feature_extraction.PSDFeatureExtractor(
        board.get_sampling_rate()
    )
    with board:
        average = pre_experiment(board, psd_feature_extractor, band_power_chart)
        print(f"Average band power 10-12Hz = {average}")
        for _ in range(0, 10):
            run_single_trial(
                board,
                psd_feature_extractor,
                band_power_chart,
                one_dim_experiment,
                average,
            )
            print("Waiting 3 seconds before next trial")
            time.sleep(3)

            print("Resetting GUI")
            one_dim_experiment.reset()


# TODO: add a count down before experiment start


if __name__ == "__main__":
    main()
