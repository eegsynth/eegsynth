#!/usr/bin/env python3

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QFormLayout)
from PyQt5.QtCore import QTimer
from pyqtgraph import PlotWidget
import pyqtgraph as pg
import numpy as np


class View(QMainWindow):

    def __init__(self, model, controller):
        
        super().__init__()

        self._model = model
        self._controller = controller
        
        pg.setConfigOptions(antialias=True)

        # Specify the application layout.
        #################################

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

        # Set timer for breathingplot (update plot every 100 msec).
        self.breathingplot_timer = QTimer()
        self.breathingplot_timer.timeout.connect(self.plot_breathing)
        self.breathingplot_timer.start(100)    # in msec

        # Initiate variables.
        self.breathingsignal = self.breathingplot.plot()
        self.powerspectrum = self.spectralplot.plot()
        
        # Define the plotting methods.
        ##############################
        
        # Connect methods to signals emitted by the model.
        self._model.psd_changed.connect(self.plot_psd)
        self._model.biofeedback_changed(self.plot_biofeedback)

    def plot_breathing(self):
        # If window or channel are updated, the update will take effect on the
        # first subsequent call of this method.
        header = self._model.ftc.getHeader()
        current_idx = header.nSamples
        sfreq = header.fSample
        beg = current_idx - self._model.window * sfreq
        end = current_idx - 1
        data = self._model.ftc.getData([beg, end])[:, self._model.channel]
        time = np.linspace(-self._model.window, 0, self._model.window * sfreq)
        self.breathingsignal.setData(time, data)


    def plot_psd(self, psd):
        # Update the power spectrum.
        self.powerspectrum.setData(self._model.freqs, psd)


    def plot_biofeedback(self, biofeedback):
        pass
