import time

import PySimpleGUI as sg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np


class LinePlot:
    def __init__(self, canvas: sg.tk.Canvas):
        self.canvas = canvas

        fig, self.axes = plt.subplots()
        # self.axes.grid(True)
        self.figure = FigureCanvasTkAgg(fig, self.canvas)
        self.figure.draw()
        self.figure.get_tk_widget().pack(side="top", fill="both", expand=1)

    def update(self, x: np.array, y: np.array):
        self.axes.cla()
        # self.axes.grid(True)
        self.axes.plot(x, y)
        self.figure.draw()


if __name__ == "__main__":
    layout = [
        [sg.Canvas(size=(640, 480), key="-CANVAS-")],
    ]

    # create the form and show it without the plot
    window = sg.Window(
        "Demo Application - Embedding Matplotlib In PySimpleGUI", layout, finalize=True
    )

    canvas_elem = window["-CANVAS-"]
    canvas = canvas_elem.TKCanvas
    line_plot = LinePlot(canvas)

    while True:
        time.sleep(0.033)
        x = range(0, 100)
        y = np.random.rand(100)
        line_plot.update(x, y)
