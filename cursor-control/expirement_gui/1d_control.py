import time
from typing import List, Tuple

import PySimpleGUI as sg


class Cursor:
    def __init__(self, canvas: sg.tk.Canvas, radius: int = 10):
        self.canvas = canvas
        self.radius = radius
        self.diameter = radius * 2
        self.cursor = self.canvas.create_oval(
            0, 0, self.diameter, self.diameter, fill="white"
        )

    def move_to(self, x: int, y: int) -> None:
        """
        Important: (0, 0) marks the upper left corner of the canvas, right is positive x, down is positive y

        :param x: x-coordinate in pixels
        :param y: y-coordinate in pixel
        """
        self.canvas.move(self.cursor, x, y)

    def move_by(self, x: int, y: int):
        pass

    def get_center(self) -> Tuple[float, float, float, float]:
        return self.canvas.coords(self.cursor)


class OneDimensionControlExperiment:
    def __init__(self):
        layout = [[sg.Canvas(size=(400, 800), background_color="black", key="canvas")]]
        self.window = sg.Window(
            "1D Cursor Control Experiment",
            layout,
            finalize=True,
            disable_close=True,
        )
        self.canvas: sg.tk.Canvas = self.window["canvas"].TKCanvas
        self.cursor = Cursor(self.canvas)

    def update(self):
        self.window.read(timeout=0)

    def close(self):
        self.window.close()


if __name__ == "__main__":
    experiment = OneDimensionControlExperiment()
    y = 0
    while True:
        y += 1
        experiment.update()
        experiment.cursor.move_to(0, y)
        time.sleep(0.25)
