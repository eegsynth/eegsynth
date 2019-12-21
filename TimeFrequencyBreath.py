# -*- coding: utf-8 -*-
"""
Created on Fri Oct 25 18:56:24 2019

@author: John Doe
"""

from scipy.signal import decimate, detrend
from scipy.interpolate import interp1d
from numpy.fft import rfft
import matplotlib.pyplot as plt
import numpy as np
from spectrum import arburg, arma2psd

path = r"C:\Users\u117148\surfdrive\Beta\Data\RESP\Bitalino\active_belt_comparison_10_6_4.txt"
data = np.loadtxt(path)
sfreq = 1000
signal = data[:, -1]


#fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
#fig.suptitle("Paced Breathing (10, 6, 4 breath per minute) at Rest")
#ax1.plot(data[:, -2])
#ax1.set_title("Piezo Belt (90€)")
#ax2.plot(data[:, -1])
#ax2.set_title("Respiratory Inductance Plethysmography Belt (900€)")


# reducing the sampling rate by half has no effect on the frequency resolution
# (width of frequency bins), merely on the highest frequency that can be
# estimated (Nyquist)
signal = decimate(signal, 500, ftype="fir")
sfreq = int(np.rint(sfreq / 500))

# determine width of processing window, t is the only parameter that influences
# frequency resolution
t = 30
window = int(t * sfreq)


# time-frequency
###############################################################################

block = 0
stride = int(np.rint(1 * sfreq))
# FFT returns (sfreq/2) / (1/t) + 1 = window/2 + 1 power estimates for
# frequencies in range 0 to sfreq/2, with one frequency bin being 1/t wide
nrows_fft = int(window / 2 + 1)
nrows_burg = int(window / 2)
# calculate how often the shifted window fits into the signal
overlap = int(window - stride)
ncols = int(np.floor((signal.size - overlap) / (window - overlap)))
pfft_all = np.zeros((nrows_fft, ncols))
pburg_all = np.zeros((nrows_burg, ncols))

while block * stride + window <= signal.size:
    beg = block * stride
    end = block * stride + window
    
    dat = signal[beg:end]
    
    dat = detrend(dat)
    dat *= np.hanning(window)
    
    AR, rho, _ = arburg(dat, order=16)
    pburg = arma2psd(AR, rho=rho, NFFT=window)
    pburg = np.flip(pburg[t:])
    pburg_all[:, block] = pburg
    
    pfft = rfft(dat, window, norm=None)
    pfft_all[:, block] = abs(pfft)
    
    block += 1

# plot FFT and Burg spectogram
freqs = np.fft.rfftfreq(window, 1 / sfreq)
#fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, sharey=True)
#ax1.pcolormesh(range(pfft_all.shape[1]), freqs, pfft_all)
#ax1.set_ylabel("Frequency")
#ax2.pcolormesh(range(pburg_all.shape[1]), freqs, pburg_all)
#ax2.set_xlabel(f"processing iteration of {t} sec window shifted by "
#               f"{int(stride / sfreq)} sec")
#ax2.set_ylabel("Frequency")

fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, sharey=True)
ax1.set_title("Piezo Belt (90€)")
ax1.set_ylabel("Frequency")
ax1.pcolormesh(range(pburg_all.shape[1]), freqs, pburg_all)
ax2.set_title("Respiratory Inductance Plethysmography Belt (900€)")
ax2.pcolormesh(range(pburg_all.shape[1]), freqs, pburg_all)
ax2.set_xlabel(f"processing iteration of {t} sec window shifted by "
               f"{int(stride / sfreq)} sec")
ax2.set_ylabel("Frequency")