import os
import sys
import time
from dataclasses import dataclass
from typing import List
import csv

import board_reader
import expirement_gui.one_dim_control as one_dim
import expirement_gui.tk_plots as tk_plots
import feature_extraction

channels = {"o1": 1, "c3": 2, "fp2": 3, "fp1": 4, "c4": 5, "cz": 6, "fz": 7, "o2": 8}
PRE_EXPERIMENT_AVG_TIME_S = 5
SAMP_RATE = 250
BAND_FEATURE_LOW_FREQ = 10
BAND_FEATURE_HIGH_FREQ = 12
TRIAL_LENGTH_S = 10
NUM_TRIALS = 20


@dataclass
class Location:
    index: int
    name: str
    image_fp: str


LOCATIONS: List[Location] = []
with open("../locations.csv", "r") as locations_csv:
    locations_reader = csv.reader(locations_csv)
    for row in locations_reader:
        if row[0] != "index":
            LOCATIONS.append(
                Location(
                    int(row[0]),
                    row[1],
                    os.path.abspath(os.path.join("../location-images", row[2])),
                )
            )


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
    location: Location,
) -> List[float]:
    band_power_values = []

    print("Starting experiment")
    time_start = time.time()
    while (
        not one_dim_experiment.top_target_reached
        and not one_dim_experiment.bottom_target_reached
    ):  # while neither target has been hit
        one_dim_experiment.write_status_text(
            f"Select destination or move to next option"
        )
        one_dim_experiment.set_destination_option(location.name, location.image_fp)

        time.sleep(0.1)  # let another tenth of a second worth of data accrue
        band_power_feature = get_psd_feature(board, psd_extractor, data_len_s=3)
        print(
            f"Band power {BAND_FEATURE_LOW_FREQ}-{BAND_FEATURE_HIGH_FREQ}Hz for last {3} seconds: {band_power_feature} - compared against average {band_power_avg}"
        )
        band_power_values.append(band_power_feature)
        chart_bands(band_power_feature, psd_extractor, band_power_chart)
        psd_chart.plot_psd(psd_extractor.psd)
        velocity = 0
        if band_power_feature < 1.2:
            velocity = -150
        if band_power_feature > 1.8:
            velocity = 50
        if band_power_feature > 2.1:
            velocity = 200
        if band_power_feature > 4:
            velocity = 400
        # if band_power_feature > band_power_avg:
        #     one_dim_experiment.cursor.set_velocity(150)  # down
        # else:
        #     one_dim_experiment.cursor.set_velocity(-150)  # up
        one_dim_experiment.cursor.set_velocity(velocity)
        one_dim_experiment.update()

    if one_dim_experiment.top_target_reached:
        print("Reached top target")
        # TODO send control signals based on location
    elif one_dim_experiment.bottom_target_reached:
        print("Hit bottom target")

    one_dim_experiment.cursor.set_velocity(0)

    return band_power_values


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
    psd_chart = tk_plots.PSDPlot(
        one_dim_experiment.plots_canvas,
        highlight_region=(BAND_FEATURE_LOW_FREQ, BAND_FEATURE_HIGH_FREQ),
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
        for location in LOCATIONS:
            run_single_trial(
                board,
                psd_feature_extractor,
                band_power_chart,
                psd_chart,
                one_dim_experiment,
                average,
                location,
            )

            print("Waiting 3 seconds before next trial")
            time.sleep(3)

            print("Resetting GUI")
            one_dim_experiment.reset()


if __name__ == "__main__":
    main()
