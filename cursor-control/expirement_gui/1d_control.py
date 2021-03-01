import time
from dataclasses import dataclass
from typing import Tuple, Union

import PySimpleGUI as sg

DEFAULT_CURSOR_RADIUS = 10


@dataclass
class Point:
    """
    Represents a point on the 2D tk.Canvas, where (0, 0) marks the upper left corner of the canvas, right is positive x,
     down is positive y. Integer values represent pixels.
    """

    x: Union[int, None] = None
    y: Union[int, None] = None


class Cursor:
    def __init__(self, canvas: sg.tk.Canvas, radius: int = DEFAULT_CURSOR_RADIUS):
        self.canvas = canvas
        self.radius = radius
        self.diameter = radius * 2
        self.cursor = self.canvas.create_oval(
            0, 0, self.diameter, self.diameter, fill="white"
        )
        # self.move_by(200, 0)

    def move_to(self, point: Point) -> None:
        """
        Move the cursor *center* to the specified point.
        :param point: a None value for x or y means the current value is retained
        """
        # handle None value in point
        x = point.x if point.x is not None else self.get_center().x
        y = point.y if point.y is not None else self.get_center().y

        # shift to cursor center
        x = x - self.radius - 1
        y = y - self.radius - 1

        self.canvas.moveto(self.cursor, x, y)

    def move_by(self, x: int = 0, y: int = 0):
        self.canvas.move(self.cursor, x, y)

    def get_center(self) -> Point:
        x1, y1, x2, y2 = self.canvas.coords(self.cursor)
        return Point(x1 + self.radius, y1 + self.radius)


class VelocityCursor(Cursor):
    """
    Cursor that moves over time according to its velocity in pixels per second. Uses real time (wall-clock time) so that
    changes in updating rate (framerate) do not affect positional correctness.
    """

    # TODO support x direction
    def __init__(self, canvas: sg.tk.Canvas, radius: int = DEFAULT_CURSOR_RADIUS):
        super().__init__(canvas, radius)
        self.y_velocity: int = 0  # pixels per second, negative is up, positive is down
        self.y_center: float = (
            self.get_center().y
        )  # need to keep a high precision location for fractional movements
        self.last_update_ns: Union[int, None] = None

    def update(self):
        if self.last_update_ns is None:  # first update
            self.last_update_ns = time.time_ns()
            return

        current_ns = time.time_ns()
        time_difference_ns = current_ns - self.last_update_ns
        time_difference_s = self.nano_to_base(time_difference_ns)
        pixels_to_move = time_difference_s * self.y_velocity
        self.y_center += pixels_to_move
        self.move_to(Point(y=int(self.y_center)))

        self.last_update_ns = current_ns

    def move_to(self, point: Point) -> None:
        self.y_center = y = point.y if point.y is not None else self.get_center().y
        super().move_to(point)

    def change_velocity_by(self, y_velocity: int):
        self.y_velocity += y_velocity

    @staticmethod
    def nano_to_base(time_ns: int) -> float:
        return time_ns / 10e9


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
        self.cursor = VelocityCursor(self.canvas)
        self.cursor.move_to(Point(200, 400))

    def update(self):
        self.cursor.update()
        self.window.read(timeout=0)

    def close(self):
        self.window.close()


if __name__ == "__main__":
    experiment = OneDimensionControlExperiment()
    experiment.cursor.change_velocity_by(15)
    while True:
        try:
            time.sleep(0.5)
            experiment.update()
        except KeyboardInterrupt:
            break
    print(experiment.cursor.get_center())
