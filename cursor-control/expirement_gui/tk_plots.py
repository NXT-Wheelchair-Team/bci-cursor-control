import time
from typing import List, Tuple

import PySimpleGUI as sg
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import brainflow as bf


class TkPlot:
    def __init__(self, canvas: sg.tk.Canvas):
        self.canvas = canvas
        fig, self.axes = plt.subplots()
        self.figure = FigureCanvasTkAgg(fig, self.canvas)
        self.figure.draw()
        self.figure.get_tk_widget().pack(side="top", fill="both", expand=1)


class LinePlot(TkPlot):
    """
    Wrapper around matplotlib.pyplot.plot for Tk. Designed to be updated many times within the same canvas.
    """

    def __init__(self, canvas: sg.tk.Canvas):
        super(LinePlot, self).__init__(canvas)

    def plot(self, *args, **kwargs):
        self.axes.cla()
        self.axes.plot(*args, **kwargs)
        self.figure.draw()


class PSDPlot(TkPlot):
    def __init__(
        self,
        canvas: sg.tk.Canvas,
        y_label: str = "Power",
        x_label: str = "Frequency (Hz)",
        title: str = "Power Spectral Density",
        y_min: float = 1e-6,
        y_max: float = 1,
        x_min: float = 1,
        x_max: float = 30,
        highlight_region: Tuple[float, float] = (1, 30),
    ):
        super(PSDPlot, self).__init__(canvas)
        self.y_label = y_label
        self.x_label = x_label
        self.title = title
        self.y_min = y_min
        self.y_max = y_max
        self.x_min = x_min
        self.x_max = x_max
        self.highlight_region = highlight_region

    def _set_text(self):
        self.axes.set_title(self.title)
        self.axes.set_ylabel(self.y_label)
        self.axes.set_xlabel(self.x_label)

    def plot_psd(self, psd: Tuple[bf.NDArray[bf.Float64], bf.NDArray[bf.Float64]]):
        self.axes.cla()
        self.axes.set_yscale("log")
        self._set_text()
        self.axes.plot(psd[1], psd[0])
        self.axes.set_ylim([self.y_min, self.y_max])
        self.axes.set_xlim([self.x_min, self.x_max])
        self.axes.axvspan(
            self.highlight_region[0], self.highlight_region[1], color="green", alpha=0.5
        )
        self.figure.draw()


class BandPowerChart(TkPlot):
    """
    Wrapper around matplotlib.pyplot.bar for Tk. Designed to be updated many times within the same canvas.
    """

    def __init__(
        self,
        canvas: sg.tk.Canvas,
        y_min: float,
        y_max: float,
        band_labels: List[str],
        y_label: str = "Power spectral density",
        title: str = "Band Power",
    ):
        super(BandPowerChart, self).__init__(canvas)
        self.y_min = y_min
        self.y_max = y_max
        self.band_labels = band_labels
        self.x_locs = np.arange(len(self.band_labels))
        self.y_label = y_label
        self.title = title

    def _set_text(self):
        self.axes.set_title(self.title)
        self.axes.set_ylabel(self.y_label)
        self.axes.set_xticks(self.x_locs)
        self.axes.set_xticklabels(self.band_labels)

    def bar(self, band_values: List[float], *args, **kwargs):
        assert len(band_values) == len(self.band_labels)
        self.axes.cla()
        self._set_text()
        self.axes.bar(self.x_locs, band_values, *args, **kwargs)
        self.axes.set_ylim([self.y_min, self.y_max])
        self.figure.draw()


if __name__ == "__main__":
    layout = [
        [
            sg.Canvas(size=(640, 480), key="line"),
        ],
        [
            sg.Canvas(size=(640, 480), key="bar"),
        ],
    ]

    # create the form and show it without the plot
    window = sg.Window(
        "Demo Application - Embedding Matplotlib In PySimpleGUI", layout, finalize=True
    )

    canvas_elem_line = window["line"]
    canvas_line = canvas_elem_line.TKCanvas
    line_plot = PSDPlot(canvas_line)

    canvas_elem_bar = window["bar"]
    canvas_bar = canvas_elem_bar.TKCanvas
    bar_plot = BandPowerChart(canvas_bar, 0, 1, ["alpha"])

    while True:
        time.sleep(0.01)
        x = range(0, 100)
        y = np.random.rand(100)
        bar_heights = np.random.rand(1)
        line_plot.plot_psd((y, x))
        bar_plot.bar(bar_heights)
