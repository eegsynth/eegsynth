# -*- coding: utf-8 -*-
"""
Spyder Editor

Dies ist eine temporäre Skriptdatei.
"""

import matplotlib.pyplot as plt
import numpy as np
from astropy.timeseries import LombScargle

fig, (ax0, ax1) = plt.subplots(nrows=2, ncols=1)

path = r"C:\Users\JohnDoe\Desktop\peaks.csv"
peaks = np.loadtxt(path, skiprows=1)

ibi = np.ediff1d(peaks, to_begin=0)
ax0.plot(ibi)

lombfreq, lombp = LombScargle(peaks, ibi).autopower(minimum_frequency=0.,
                             maximum_frequency=0.4)
ax1.plot(lombfreq, lombp)




