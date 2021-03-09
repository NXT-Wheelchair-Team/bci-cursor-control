import time
from typing import List

import PySimpleGUI as sg
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


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
    line_plot = LinePlot(canvas_line)

    canvas_elem_bar = window["bar"]
    canvas_bar = canvas_elem_bar.TKCanvas
    bar_plot = BandPowerChart(
        canvas_bar, 0, 1, ["alpha", "beta", "gamma", "foo", "bar"]
    )

    while True:
        time.sleep(0.01)
        x = range(0, 100)
        y = np.random.rand(100)
        bar_height = np.random.rand(1)
        line_plot.plot(x, y, alpha=0.5)
        bar_plot.bar([0.2, 0.3, 0.1, 0.9, 0.7])
