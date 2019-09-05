#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  5 09:53:26 2019

@author: pi
"""

import sys
import matplotlib.pyplot as plt
from resp_online_zerocross_dev import extrema_signal
# need to be in eegsynth/lib for this import
sys.path.insert(0, '/home/pi/eegsynth/lib')
import EDF

path = '/home/pi/eegsynth/patches/biofeedback/recordsignal.edf'
reader = EDF.EDFReader()
reader.open(path)
# only one channel has been recorded
signal = reader.readSignal(0)

extrema_signal(signal, 1000, enable_plot=True)


#plt.plot(signal)