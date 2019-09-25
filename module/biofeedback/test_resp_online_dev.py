#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  5 09:53:26 2019

@author: pi
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
from filters import butter_bandpass_filter as butter_bp
from scipy.signal import detrend, butter, lfilter_zi, lfilter, filtfilt
from resp_online_zerocross_dev import extrema_signal


# EDF files ###################################################################

## need to be in eegsynth/lib for this import
#sys.path.insert(0, '/home/pi/eegsynth/lib')
#import EDF
#
#path = '/home/pi/eegsynth/patches/biofeedback/recordsignal.edf'
#reader = EDF.EDFReader()
#reader.open(path)
## only one channel has been recorded
#signal = reader.readSignal(0)



# text files ##################################################################

path = r'C:\Users\JohnDoe\surfdrive\Beta\data\RESP\Bitalino\opensignals_201805284661_2019-04-29_12-01-47.txt'
channel = -1
sfreq = 10
signal = np.loadtxt(path)[:, channel]

# real-time simulation of continuous filtering
nyq = 0.5 * sfreq
low = 0.05 / nyq
high = 0.5 / nyq
b, a = butter(2, [low, high], btype='band')
zi = lfilter_zi(b, a)
window_size = int(np.ceil(0.1 * sfreq))
signal_filt = []
beg = 0
end = window_size
while end < len(signal):

    dat = signal[beg:end]
    filt, zi = lfilter(b, a, dat, axis=-1, zi=zi)
    signal_filt.extend(filt)
    
    beg += window_size
    end += window_size
    
signal_filt_online = np.asarray(signal_filt)

# filter signal offline
signal_filt_offline = filtfilt(b, a, signal, method='pad')

plt.plot(signal_filt_online)
plt.plot(signal_filt_offline)


#extrema_signal(signal, sfreq, enable_plot=True)
