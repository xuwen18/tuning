import numpy as np

import matplotlib
matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qtagg import (
    FigureCanvasQTAgg as FigureCanvas
)
from matplotlib.figure import Figure

# from PySide6.QtCore    import Qt
from PySide6.QtWidgets import QFrame, QVBoxLayout

X_LABEL = 'time (ms)'
Y_LABEL = 'pressure (mbar)'

class Canvas(QFrame):

    def __init__(self, length=50, parent=None):
        super().__init__(parent)
        self.length = length

        layout = QVBoxLayout()
        self.setLayout(layout)
        self.layout().setContentsMargins(0,0,0,0)
        self.layout().setSpacing(0)

        # self.fig = Figure(figsize=(width, height), layout='constrained')
        self.fig = Figure(layout='constrained')
        self.fc = FigureCanvas(figure=self.fig)
        # self.sc = QScrollBar(Qt.Orientation.Horizontal)
        layout.addWidget(self.fc)
        # layout.addWidget(self.sc)

        self.ax = self.fig.add_subplot()

        self.reset()

    def reset(self):
        self.x1 = np.array([0.0])
        self.y1 = np.array([0.0])
        self.y2 = np.array([0.0])

        self.ax.set_xlabel(X_LABEL)
        self.ax.set_ylabel(Y_LABEL)
        self.ax.set_ylim(bottom=0)
        self.ax.grid()
        self.fc.draw()

    def animate(self, nextX1, nextY1, nextY2):

        self.x1 = np.append(self.x1, nextX1)
        self.y1 = np.append(self.y1, nextY1)
        self.y2 = np.append(self.y2, nextY2)

        self.ax.clear()
        self.ax.plot(self.x1[-self.length:], self.y1[-self.length:])
        self.ax.plot(self.x1[-self.length:], self.y2[-self.length:])
        self.ax.set_xlabel(X_LABEL)
        self.ax.set_ylabel(Y_LABEL)
        self.ax.set_ylim(bottom=0)
        self.ax.grid()
        self.fc.draw()

