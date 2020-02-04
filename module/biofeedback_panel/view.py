#!/usr/bin/env python3

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QFormLayout, QLabel, QSlider, QLineEdit,
                             QGroupBox, QComboBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor
from pyqtgraph import (PlotWidget, ScatterPlotItem, PlotCurveItem,
                       InfiniteLine, LinearRegionItem)
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
        self.windowsize_label = QLabel(f"Window size ({self._model.window} seconds)")
        self.windowsize_input = QSlider()
        self.windowsize_input.setTracking(False)
        self.windowsize_input.setOrientation(Qt.Horizontal)
        self.windowsize_input.setTickPosition(QSlider.TicksBelow)
        self.windowsize_input.setTickInterval(1)
        self.windowsize_input.setMinimum(1)
        self.windowsize_input.setMaximum(12)
        self.breathingplot_menu.addRow(self.windowsize_label,
                                       self.windowsize_input)
        self.windowsize_input.valueChanged.connect(self._model.set_window)
        lambdafn = lambda : self.windowsize_label.setText(f"Window size ({self._model.window} seconds)")
        self.windowsize_input.valueChanged.connect(lambdafn)

        self.spectralplot = PlotWidget()
        self.spectralplot_menu = QGroupBox("Biofeedback thresholds")
        self.spectralplot_menuitems = QHBoxLayout()
        self.rewardmin_label = QLabel(f"Min reward: {round(self._model.lowreward * 60, 2)} bpm")
        self.rewardmax_label = QLabel(f"Max reward: {round(self._model.upreward * 60, 2)} bpm")
        self.totalmin_label = QLabel(f"Min total: {round(self._model.lowtotal * 60, 2)} bpm")
        self.totalmax_label = QLabel(f"Max total: {round(self._model.uptotal * 60, 2)} bpm")
        self.spectralplot_menuitems.addWidget(self.rewardmin_label)
        self.spectralplot_menuitems.addWidget(self.rewardmax_label)
        self.spectralplot_menuitems.addWidget(self.totalmin_label)
        self.spectralplot_menuitems.addWidget(self.totalmax_label)
        self.spectralplot_menu.setLayout(self.spectralplot_menuitems)
        
        self.biofeedbackplot = PlotWidget()
        self.biofeedbackplot_menu = QGroupBox("Biofeedback mapping")
        self.biofeedbackplot_menuitems = QVBoxLayout()
        self.biofeedbacktarget_label = QLabel(f"Target: {round(self._model.biofeedbacktarget, 2)}")
        self.biofeedbackplot_menuitems.addWidget(self.biofeedbacktarget_label)
        self.biofeedbackplot_menu.setLayout(self.biofeedbackplot_menuitems)
        self.biofeedbackmapping_label = QLabel("Mapping:")
        self.biofeedbackmapping_input = QComboBox()
        self.biofeedbackmapping_input.addItem("linear")
        self.biofeedbackmapping_input.addItem("exponential")
        self.biofeedbackmapping_input.currentTextChanged.connect(self._model.set_biofeedbackmapping)
        self.biofeedbackmapping_input.currentTextChanged.connect(self.plot_biofeedbackmapping)
        self.biofeedbackplot_menuitems.addWidget(self.biofeedbackmapping_label)
        self.biofeedbackplot_menuitems.addWidget(self.biofeedbackmapping_input)
        # Initialize with default value
        self._model.set_biofeedbackmapping(self.biofeedbackmapping_input.currentText())

        self.centralwidget = QWidget()
        self.setCentralWidget(self.centralwidget)

        self.vlayout0 = QVBoxLayout(self.centralwidget)
        self.hlayout0 = QHBoxLayout()
        self.hlayout1 = QHBoxLayout()
        self.hlayout2 = QHBoxLayout()

        self.hlayout1.addWidget(self.spectralplot)
        self.hlayout1.addWidget(self.biofeedbackplot)

        self.hlayout0.addLayout(self.breathingplot_menu)
        self.hlayout2.addWidget(self.spectralplot_menu)
        self.hlayout2.addWidget(self.biofeedbackplot_menu)

        self.vlayout0.addWidget(self.breathingplot)
        self.vlayout0.addLayout(self.hlayout0)
        self.vlayout0.addLayout(self.hlayout1)
        self.vlayout0.addLayout(self.hlayout2)

        self.vlayout0.setStretch(0, 5)
        self.vlayout0.setStretch(1, 1)
        self.vlayout0.setStretch(2, 10)
        self.vlayout0.setStretch(3, 1)

        # Configure the breathingplot.
        self.breathingsignal = PlotCurveItem()
        self.breathingplot.addItem(self.breathingsignal)
        self.breathingplot.getAxis("bottom").setLabel("seconds")
        
        # Configure the spectralplot.
        self.powerspectrum = PlotCurveItem()
        self.powerspectrum.setZValue(2)
        self.spectralplot.addItem(self.powerspectrum)
        
        self.spectralbounds = [0, 1]
        self.spectralplot.setRange(xRange=self.spectralbounds)
        # Convert frequencies [0, 1] to rate [0, 60]
        self.spectralplot.getAxis("bottom").setScale(60)
        self.spectralplot.getAxis("bottom").setLabel("breathing rate")
        self.spectralplot.getAxis("left").setLabel("power")
        
        rewardrangebrush = QBrush(QColor(0, 255, 0, 50))
        self.rewardrange = LinearRegionItem()
        # Fix the possible range to the range of frequencies [0, 1] at sampling
        # rate of 2 Hz.
        self.rewardrange.setBounds([0, 1])
        # Initialize the range with the default values.
        self.rewardrange.setRegion([self._model.lowreward, self._model.upreward])
        self.rewardrange.sigRegionChangeFinished.connect(self._model.set_lowreward)
        self.rewardrange.sigRegionChangeFinished.connect(self._model.set_upreward)
        lambdafn = lambda : self.rewardmin_label.setText(f"Min reward: {round(self._model.lowreward * 60, 2)} bpm")
        self.rewardrange.sigRegionChangeFinished.connect(lambdafn)
        lambdafn = lambda : self.rewardmax_label.setText(f"Max reward: {round(self._model.upreward * 60, 2)} bpm")
        self.rewardrange.sigRegionChangeFinished.connect(lambdafn)
        self.rewardrange.setBrush(rewardrangebrush)
        self.rewardrange.setZValue(2)
        self.spectralplot.addItem(self.rewardrange)
        
        self.totalrange = LinearRegionItem()
        # Fix the possible range to the range of frequencies [0, 1] at sampling
        # rate of 2 Hz.
        self.totalrange.setBounds([0, 1])
        # Initialize the range with the default values.
        self.totalrange.setRegion([self._model.lowtotal, self._model.uptotal])
        self.totalrange.sigRegionChangeFinished.connect(self._model.set_lowtotal)
        self.totalrange.sigRegionChangeFinished.connect(self._model.set_uptotal)
        lambdafn = lambda : self.totalmin_label.setText(f"Min total: {round(self._model.lowtotal * 60, 2)} bpm")
        self.totalrange.sigRegionChangeFinished.connect(lambdafn)
        lambdafn = lambda : self.totalmax_label.setText(f"Max total: {round(self._model.uptotal * 60, 2)} bpm")
        self.totalrange.sigRegionChangeFinished.connect(lambdafn)
        self.totalrange.setZValue(1)
        self.spectralplot.addItem(self.totalrange)
        
        # Configure the biofeedbackplot.
        self.biofeedbackbounds = [0, self._model.biofeedbacktarget + 1]
        self.biofeedbackplot.setRange(xRange=self.biofeedbackbounds,
                                      yRange=[0, 1])
        self.biofeedbackplot.setLimits(xMin=0)
        
        self.biofeedbackscatter = ScatterPlotItem()
        self.biofeedbackscatter.setSymbol("+")
        self.biofeedbackscatter.setSize(50)
        self.biofeedbackscatter.setBrush((255, 165, 0))    # tuple with RGB values
        self.biofeedbackplot.addItem(self.biofeedbackscatter)
        
        self.biofeedbackfunction = PlotCurveItem()
        self.biofeedbackplot.addItem(self.biofeedbackfunction)
        
        self.biofeedbacktarget = InfiniteLine(angle=90, movable=True)
        self.biofeedbacktarget.setBounds(self.biofeedbackbounds)
        self.biofeedbacktarget.sigPositionChangeFinished.connect(self._model.set_biofeedbacktarget)
        self.biofeedbacktarget.sigPositionChangeFinished.connect(self.plot_biofeedbackmapping)
        lambdafn = lambda : self.biofeedbacktarget_label.setText(f"Target: {round(self._model.biofeedbacktarget, 2)}")
        self.biofeedbacktarget.sigPositionChangeFinished.connect(lambdafn)
        # Initialize the plot. Note that the signal must be emitted manually,
        # since InfiniteLine does not emit sigPositionChangeFinished if value
        # is set programatically.
        self.biofeedbacktarget.setValue(self._model.biofeedbacktarget)
        self.biofeedbacktarget.sigPositionChangeFinished.emit("foo")
        self.biofeedbackplot.addItem(self.biofeedbacktarget)
        
        self.biofeedbackplot.getAxis("bottom").setLabel("rewardratio (rewardrange / (totalrange - rewardrange))")
        self.biofeedbackplot.getAxis("left").setLabel("biofeedback")
        
        # Define the plotting methods.
        ##############################

        # Connect methods to signals emitted by the model.
        self._model.psd_changed.connect(self.plot_psd)
        self._model.biofeedback_changed.connect(self.plot_biofeedback)
        self._model.breathing_changed.connect(self.plot_breathing)


    def plot_breathing(self, breathing):
        # If window or channel are updated, the update will take effect on the
        # first subsequent call of this method.
        
        # Important to get these attributes simultaneously!
        data, sfreq = self._model.data, self._model.sfreq
        nsamp = len(data)
        time = np.linspace(-nsamp / sfreq, 0, nsamp)
        self.breathingsignal.setData(time, data)


    def plot_psd(self, psd):
        self.powerspectrum.setData(self._model.freqs, psd)
    

    def plot_biofeedback(self, biofeedback):
        self.biofeedbackscatter.setData([biofeedback[0]], [biofeedback[1]])
        
        
    def plot_biofeedbackmapping(self):
        # Note that the mapping needs to be re-plotted when the target
        # changes as well as when the mapping changes.
        xmin = self.biofeedbackbounds[0]
        xmax = self.biofeedbackbounds[1]
        xvals = np.linspace(xmin, xmax, (xmax - xmin) * 100)
        yvals = [self._controller.biofeedback_function(i, self._model.biofeedbackmapping) for i in xvals]
        self.biofeedbackfunction.setData(xvals, yvals)
