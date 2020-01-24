#!/usr/bin/env python3

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QFormLayout)
from PyQt5.QtCore import QTimer
from pyqtgraph import PlotWidget
import numpy as np


class View(QMainWindow):

    def __init__(self, model, controller):
        super().__init__()

        self._model = model
        self._controller = controller

        # Specify the application layout.
        ################################

        self.breathingplot = PlotWidget()
        self.breathingplot_menu = QFormLayout()
        self.spectralplot = PlotWidget()
        self.spectralplot_menu = QFormLayout()
        self.biofeedbackplot = PlotWidget()
        self.biofeedbackplot_menu = QFormLayout()

        self.centralwidget = QWidget()
        self.setCentralWidget(self.centralwidget)

        self.vlayout0 = QVBoxLayout(self.centralwidget)
        self.hlayout0 = QHBoxLayout()
        self.hlayout1 = QHBoxLayout()
        self.hlayout2 = QHBoxLayout()

        self.hlayout1.addWidget(self.spectralplot)
        self.hlayout1.addWidget(self.biofeedbackplot)

        self.hlayout0.addLayout(self.breathingplot_menu)
        self.hlayout2.addLayout(self.spectralplot_menu)
        self.hlayout2.addLayout(self.biofeedbackplot_menu)

        self.vlayout0.addWidget(self.breathingplot)
        self.vlayout0.addLayout(self.hlayout0)
        self.vlayout0.addLayout(self.hlayout1)
        self.vlayout0.addLayout(self.hlayout2)

        self.vlayout0.setStretch(0, 5)
        self.vlayout0.setStretch(1, 1)
        self.vlayout0.setStretch(2, 10)
        self.vlayout0.setStretch(3, 1)

        # Set timer for breathingplot (update plot every 100 msec)
        breathingplot_timer = QTimer()
        breathingplot_timer.timeout.connect(self.plot_breathing)
        breathingplot_timer.start(100)    # in msec

        # Initiate variables.
        self.breathing = np.zeros(self._model.window)
        self.breathingwindow = np.linspace(-self._model.window / self._model.sfreq,
                                           0, self._model.window * self._model.sfreq)


    # Define the plotting methods.
    ##############################

    def plot_breathing(self):

        self.breathing = self._model.ft_client.getData(self._model.window)
        self.breathingplot.plot(self.breathing, self.breathingwindow)


    def plot_spectral(self):
        pass


    def plot_biofeedback(self):
        pass


    # Display biofeedback mapping with current breathing estimate.


    # Display breathing spectrum.





