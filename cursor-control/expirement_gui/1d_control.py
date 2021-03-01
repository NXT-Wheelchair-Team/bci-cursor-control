import time
from dataclasses import dataclass
from typing import Tuple, Union

import PySimpleGUI as sg


@dataclass
class Point:
    """
    Represents a point on the 2D tk.Canvas, where (0, 0) marks the upper left corner of the canvas, right is positive x,
     down is positive y. Integer values represent pixels.
    """

    x: Union[int, None] = None
    y: Union[int, None] = None


class Cursor:
    def __init__(self, canvas: sg.tk.Canvas, radius: int = 10):
        self.canvas = canvas
        self.radius = radius
        self.diameter = radius * 2
        self.cursor = self.canvas.create_oval(
            0, 0, self.diameter, self.diameter, fill="white"
        )
        # self.move_by(200, 0)

    def move_to(self, point: Point) -> None:
        """
        Move to the specified point.
        :param point: a None value for x or y means the current value is retained
        """
        x = point.x if point.x is not None else self.get_center().x
        y = point.y if point.y is not None else self.get_center().y
        self.canvas.moveto(self.cursor, x, y)

    def move_by(self, x: int = 0, y: int = 0):
        self.canvas.move(self.cursor, x, y)

    def get_center(self) -> Point:
        x1, y1, x2, y2 = self.canvas.coords(self.cursor)
        return Point(x1 + self.radius, y1 + self.radius)


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
    y = 1
    experiment.cursor.move_to(Point(x=200))
    while True:
        y += 0.1
        experiment.update()
        experiment.cursor.move_by(0, y)
        time.sleep(0.033)
        if y > 10:
            break
    print(experiment.cursor.get_center())
