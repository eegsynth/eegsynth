#!/usr/bin/env python
# coding=utf-8

# ==============================================================================
# title           : gtec2wav.py
# description     : This will read Gtec file and convert it into
#                   signal for interstellar EEG transmission.
# author          : Guillaume Dumas
# date            : 2018
# version         : 2
# usage           : python gtec2wav.py
# notes           :
# python_version  : 2.7, 3.6
# license         : BSD (3-clause)
# ==============================================================================

import h5py
# import matplotlib.pyplot as plt
import pandas as pd
from scipy import signal
import numpy as np
import wave
import struct

filename = "RecordSession_YYY.MM.DD_HH.MM.SS.hdf5"
filename = "../../data/test.hdf5"

profileMin=1.0
profileMax=1.5

profileCorrection = np.loadtxt('Dwingeloo-Transmitter-Profile.txt')
profileCorrection = (1. - profileCorrection)*(profileMax-profileMin)
profileCorrection += profileMin

# Approximate positions of channels in space
layout = pd.read_csv("gtec_layout.csv", index_col=0)
definition = 9
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
    t = np.arange(0, len(data))
    p = np.polynomial.polynomial.polyfit(t, data, 3)
    data = data - np.polynomial.polynomial.polyval(t, p)
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

# plt.figure()
# # plt.plot(Samples)
# plt.plot(Samples[int(time_point*fsample):int((time_point+22)*fsample), :])
# plt.legend(layout.label.tolist())
# plt.show()


f_min = 1
f_max = 45

chan_tmp = []
scaling = 0.1
for step in np.arange(0, samples, 125):
    tmp = [np.zeros(440)]
    for ch in range(channels):
        channel = []
        original = Samples[(step):(step+249), ch]
        # plt.plot(original, 'r')
        t = np.arange(0, len(original))
        p = np.polynomial.polynomial.polyfit(t, original, 2)
        original = original - np.polynomial.polynomial.polyval(t, p)

        # One
        channel.append(np.ones(1)*scaling/250.)
        # Spectrum
        fourier = np.fft.rfft(original, 250)[f_min:f_max]
        channel.append(fourier)

        # Positions
        mask = np.zeros(30)
        mask[int(positions[ch][0])] = scaling/250.
        mask[10+int(positions[ch][1])] = scaling/250.
        mask[20+int(positions[ch][2])] = scaling/250.
        channel.append(mask)

        # Sum of all the parts
        convert = np.concatenate(channel) * profileCorrection[ch]
        # plt.plot(np.real(np.fft.ifft(np.concatenate([np.array([0]), convert[1:45], np.array(np.zeros(5+200))]), 250)))
        # plt.show()
        tmp.append(convert)
    chan_tmp.append(np.fft.irfft(np.concatenate(tmp), 44100))

global_signal = np.zeros(int(44100*len(chan_tmp)/2-44100/2))
for idx, step in enumerate(np.arange(0, len(global_signal)-44100/2, 44100/2)):
    global_signal[int(step):int(step+44100)] = global_signal[int(step):int(step+44100)] + chan_tmp[idx]

wav_signal = ((global_signal - global_signal.min())/(global_signal.max() - global_signal.min())*32767*2-32767).astype(int)

wave_output = wave.open('Gtec_polyfit_boxcar_32_pitched.wav', 'w')
wave_output.setparams((1, 2, 44100, 0, 'NONE', 'not compressed'))

SAMPLE_LEN = wav_signal.shape[0]
values = []
for i in range(0, SAMPLE_LEN):
    values.append(struct.pack('h', wav_signal[i]))

value_str = b''.join(values)
wave_output.writeframes(value_str)
wave_output.close()
