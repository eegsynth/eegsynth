# -*- coding: utf-8 -*-


from resp_online_zerocross_dev import extrema_signal
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import lfilter_zi, lfilter, butter

path = r"C:\Users\JohnDoe\surfdrive\Beta\biochill\data\pilot_Nov19\physiology\2_feedback.txt"
signal = pd.read_csv(path, delimiter='\t', usecols=[5],
                     header=None, comment='#')

sfreq = 1000
window = 0.1
window = int(np.rint(window * sfreq))
previous_dc = np.zeros(window)
previous_raw = np.zeros(window)
beg = 0
end = window
highcut = 1

# simulate online preprocessing (dc blocking)##################################
###############################################################################

# initialize filter
nyq = 0.5 * sfreq
highcut = highcut / nyq
b, a = butter(3, highcut, btype='lowpass')
zi = lfilter_zi(b, a)

centered = []

while end < len(signal):

    dat = np.asarray(signal[beg:end])
    raw = np.mean(dat)

    # add warmstart offset on first iteration (subtraction only works for
    # positive offsets)
    if beg == 0:
        previous_dc -= raw

    dcblocked = raw - previous_raw + 0.999 * previous_dc

    previous_dc = dcblocked
    previous_raw = raw

    filtered, zi = lfilter(b, a, dcblocked, zi=zi)

    centered.extend(filtered)

    # increment the indices for the next iteration
    beg += window
    end += window

# signal.plot()
# plt.plot(centered)
# plt.axhline(y=0)

# simulate online peak detection ##############################################
###############################################################################

extrema_signal(np.asarray(centered), 1000, enable_plot=True)
