import time
from typing import List, Dict

import board_reader
import expirement_gui.one_dim_control as one_dim
import expirement_gui.tk_plots as tk_plots
import feature_extraction
import matplotlib.pyplot as plt
from scipy import stats
import seaborn as sns

channels = {"o1": 1, "c3": 2, "fp2": 3, "fp1": 4, "c4": 5, "cz": 6, "fz": 7, "o2": 8}
POWER_BAND_LOW = 10
POWER_BAND_HIGH = 12
WINDOW_SIZE_SAMPLES = 256  # must be a power of two
PRE_EXPERIMENT_AVG_TIME_S = 5
SAMP_RATE = 250
BAND_FEATURE_LOW_FREQ = 11
BAND_FEATURE_HIGH_FREQ = 13
TRIAL_LENGTH_S = 10
NUM_TRIALS = 20


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
    psd_chart: tk_plots.PSDPlot,
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
    psd_chart.plot_psd(psd_extractor.psd)
    return band_power_feature


def run_single_trial(
    board: board_reader.BoardReader,
    psd_extractor: feature_extraction.PSDFeatureExtractor,
    band_power_chart: tk_plots.BandPowerChart,
    psd_chart: tk_plots.PSDPlot,
    one_dim_experiment: one_dim.OneDimensionControlExperiment,
    band_power_avg: float,
) -> List[float]:
    band_power_values = []

    print("Starting experiment")
    time_start = time.time()
    while (
        time.time() - time_start < TRIAL_LENGTH_S
        and not one_dim_experiment.target_reached
    ):
        time_remaining = int(time_start + TRIAL_LENGTH_S - time.time())
        one_dim_experiment.write_status_text(
            f"Trial in progress... {time_remaining} seconds remaining"
        )

        time.sleep(0.1)  # let another tenth of a second worth of data accrue
        band_power_feature = get_psd_feature(board, psd_extractor, data_len_s=3)
        print(
            f"Band power 10-12Hz for last {3} seconds: {band_power_feature} - compared against average {band_power_avg}"
        )
        band_power_values.append(band_power_feature)
        chart_bands(band_power_feature, psd_extractor, band_power_chart)
        psd_chart.plot_psd(psd_extractor.psd)
        velocity = 0
        if band_power_feature < 1.5:
            velocity = -150
        if band_power_feature > 4:
            velocity = 50
        if band_power_feature > 6:
            velocity = 200
        if band_power_feature > 8:
            velocity = 400
        # if band_power_feature > band_power_avg:
        #     one_dim_experiment.cursor.set_velocity(150)  # down
        # else:
        #     one_dim_experiment.cursor.set_velocity(-150)  # up
        one_dim_experiment.cursor.set_velocity(velocity)
        one_dim_experiment.update()

    print(f"Target reached: {one_dim_experiment.target_reached}")
    if not one_dim_experiment.target_reached:
        one_dim_experiment.notify_target_not_reached()
        one_dim_experiment.update()

    one_dim_experiment.cursor.set_velocity(0)

    return band_power_values


def main():
    band_power_values_all_trials: Dict[
        one_dim.OneDimensionControlExperiment.TargetPos, List[float]
    ] = {
        one_dim.OneDimensionControlExperiment.TargetPos.TOP: [],
        one_dim.OneDimensionControlExperiment.TargetPos.BOTTOM: [],
    }

    one_dim_experiment = one_dim.OneDimensionControlExperiment(num_trials=NUM_TRIALS)
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
    psd_chart = tk_plots.PSDPlot(
        one_dim_experiment.plots_canvas,
        highlight_region=(POWER_BAND_LOW, POWER_BAND_HIGH),
    )
    board = board_reader.BoardReader()  # defaults to Cyton
    board_reader.FileWriter(board)
    psd_feature_extractor = feature_extraction.PSDFeatureExtractor(
        board.get_sampling_rate()
    )
    with board:
        one_dim_experiment.write_status_text("5 second PSD averaging")
        # average = pre_experiment(
        #     board, psd_feature_extractor, band_power_chart, psd_chart
        # )
        time.sleep(3)
        average = 1
        print(f"Average band power 10-12Hz = {average}")
        for i in range(0, NUM_TRIALS):
            band_power_values = run_single_trial(
                board,
                psd_feature_extractor,
                band_power_chart,
                psd_chart,
                one_dim_experiment,
                average,
            )
            band_power_values_all_trials[one_dim_experiment.target_position].extend(
                band_power_values
            )

            print("Waiting 3 seconds before next trial")
            time.sleep(3)

            print("Resetting GUI")
            if i != NUM_TRIALS - 1:  # don't reset at end of experiment
                one_dim_experiment.reset()

        print("Experiment complete")
        print(
            f"Final results:\n"
            f"\tTop hit: {one_dim_experiment.top_hit}"
            f"\t\tBottom hit - {one_dim_experiment.bottom_hit}\n"
            f"\tNum top - {NUM_TRIALS / 2}"
            f"\t\tNum bottom - {NUM_TRIALS / 2}"
        )

        plt.close("all")
        # plt.hist(
        #     band_power_values_all_trials.values(),
        #     bins=60,
        #     range=(0, 6),
        #     label=["TOP", "BOTTOM"],
        #     density=True,
        # )
        for pos in [
            one_dim.OneDimensionControlExperiment.TargetPos.TOP,
            one_dim.OneDimensionControlExperiment.TargetPos.BOTTOM,
        ]:
            pos_data = band_power_values_all_trials[pos]
            ax: plt.Axes = sns.distplot(
                pos_data,
                hist=False,
                kde=True,
                kde_kws={"shade": True, "linewidth": 3},
                label=f"{pos} - nobs: {len(pos_data)}",
            )
            ax.set_xlim(0)
        plt.xlabel("Power Spectral Density")
        plt.ylabel("Frequency Density")
        plt.title("PSD Distribution by Target Position")
        plt.legend()
        plt.show()
        print("Top target band power stats:")
        print(
            stats.describe(
                band_power_values_all_trials[one_dim_experiment.TargetPos.TOP]
            )
        )
        print("Bottom target band power stats:")
        print(
            stats.describe(
                band_power_values_all_trials[one_dim_experiment.TargetPos.BOTTOM]
            )
        )


if __name__ == "__main__":
    main()
