# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 11:03:16 2019

@author: U117148
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import decimate, detrend, welch, lombscargle

sfreq_orig = 100
fig, axes = plt.subplots(2, 2)


peaks = np.loadtxt(r"\\CNAS.RU.NL\U117148\Desktop\peaks_test.csv", skiprows=1)
period_intp = np.loadtxt(r"\\CNAS.RU.NL\U117148\Desktop\period_test.csv",
                         skiprows=1)
period = np.ediff1d(peaks, to_begin=1)
axes[0, 0].plot(period)


# FFT on uniformly sampled heart periods (downsample to 2 Hz)
sfreq = 2
period_intp = decimate(period_intp, int(np.rint(sfreq_orig / sfreq)),
                       ftype="fir")
axes[1, 0].plot(period_intp)
freqs, psd = welch(period_intp, fs=sfreq, nperseg=int(np.rint(60 * sfreq)))
axes[1, 1].plot(freqs, psd)




# Lomb-Scargle on non-uniformly sampled heart periods
lombfreqs = np.linspace(0.0001, 1, 61)
lombpsd = lombscargle(peaks, period, freqs=lombfreqs, precenter=True)
axes[0, 1].plot(lombfreqs, lombpsd)

