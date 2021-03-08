import time

import PySimpleGUI as sg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np


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


class BarPlot(TkPlot):
    """
    Wrapper around matplotlib.pyplot.bar for Tk. Designed to be updated many times within the same canvas.
    """

    def __init__(
        self,
        canvas: sg.tk.Canvas,
    ):
        super(BarPlot, self).__init__(canvas)

    def plot(self, *args, **kwargs):
        self.axes.cla()
        self.axes.bar(*args, **kwargs)
        self.axes.set_ylim([0, 1])
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
    bar_plot = BarPlot(canvas_bar)

    while True:
        time.sleep(0.01)
        x = range(0, 100)
        y = np.random.rand(100)
        bar_height = np.random.rand(1)
        line_plot.plot(x, y, alpha=0.5)
        bar_plot.plot(0, bar_height)
