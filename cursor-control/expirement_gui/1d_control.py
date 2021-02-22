import PySimpleGUI as sg


class OneDimensionControlExperiment:
    def __init__(self):
        layout = [[sg.Canvas(size=(800, 400), background_color="black")]]

    def update(self):
        pass


if __name__ == "__main__":
    experiment = OneDimensionControlExperiment()
    while True:
        experiment.update()
