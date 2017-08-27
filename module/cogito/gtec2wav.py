#!/usr/bin/env python
# coding=utf-8

# ==============================================================================
# title           : gtec2wav.py
# description     : This will read Gtec file and convert it into
#                   signal for interstellar EEG transmission.
# author          : Guillaume Dumas
# date            : 2017
# version         : 1
# usage           : python gtec2wav.py gtecfile.hdf5
# notes           :
# python_version  : 2.7
# license         : BSD (3-clause)
# ==============================================================================

import h5py
import matplotlib.pyplot as plt
import pandas as pd
from scipy import signal
import numpy as np
from obspy.signal.detrend import polynomial
import wave
import struct

filename = "RecordSession_YYY.MM.DD_HH.MM.SS.hdf5"

# Approximate positions of channels in space
layout = pd.read_csv("gtec_layout.csv", index_col=0)
definition = 10
val = layout.loc[:, ['x', 'y', 'z']].values
val = (val - val.min())/(val.max()-val.min())*definition
positions = np.round(val).astype(int)
layout.loc[:, ['x', 'y', 'z']] = positions

# Loading the Gtec file
f = h5py.File(filename, "r")
Samples = f["RawData"]["Samples"].value

# CAR = Samples.mean(axis=1)
# Samples = Samples - np.atleast_2d(CAR).T * np.ones([1, Samples.shape[1]])

fsample = 250.
samples = Samples.shape[0]
channels = Samples.shape[1]
time_point = 226

for ch in range(channels):
    data = Samples[:, ch]
    polynomial(data, order=3, plot=False)
    Samples[:, ch] = data

sig = Samples.T
b, a = signal.butter(4, 45 / fsample, 'low', analog=True)
sig = signal.filtfilt(b, a, sig, axis=1)
b, a = signal.butter(4, 2 / fsample, 'high', analog=True)
sig = signal.filtfilt(b, a, sig, axis=1)
Q = 30.0  # Quality factor
w0 = 50/(fsample/2)  # Normalized Frequency
b, a = signal.iirnotch(w0, Q)
sig = signal.filtfilt(b, a, sig)
Samples = sig.T

plt.figure()
plt.plot(Samples)
plt.legend(layout.label.tolist())
plt.show()


f_min = 1
f_max = 45

chan_tmp = []
scaling = 0.5
for step in np.arange(0, samples, 125):
    tmp = []
    for ch in range(channels):
        channel = []
        original = Samples[(step):(step+249), ch]
        polynomial(original, order=30, plot=False)

        # One
        channel.append(np.ones(1)*scaling/250.)
        # Spectrum
        fourier = np.fft.rfft(original, 250)[f_min:f_max]
        channel.append(fourier)
        # Positions
        mask = np.zeros(30)
        mask[(positions[ch][0]-1):positions[ch][0]] = scaling/250
        mask[(10+positions[ch][1]-1):(10+positions[ch][1])] = scaling/250
        mask[(20+positions[ch][2]-1):(20+positions[ch][2])] = scaling/250
        channel.append(mask)

        # Sum of all the parts
        convert = np.concatenate(channel)
        tmp.append(convert)
    chan_tmp.append(np.fft.irfft(np.concatenate(tmp), 44100))

global_signal = np.zeros(44100*len(chan_tmp)/2-44100)
for idx, step in enumerate(np.arange(0, len(global_signal)-44100, 44100/2)):
    global_signal[step:(step+44100)] = global_signal[step:(step+44100)] + \
                                       signal.boxcar(44100) * chan_tmp[idx]

wav_signal = ((global_signal - global_signal.min())/(global_signal.max() -
              global_signal.min())*32767*2-32767).astype(int)

wave_output = wave.open('Gtec_polyfit_boxcar_32.wav', 'w')
wave_output.setparams((1, 2, 44100, 0, 'NONE', 'not compressed'))

SAMPLE_LEN = wav_signal.shape[0]
values = []
for i in range(0, SAMPLE_LEN):
    values.append(struct.pack('h', wav_signal[i]))

value_str = ''.join(values)
wave_output.writeframes(value_str)
wave_output.close()
