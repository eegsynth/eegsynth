#-*- coding: utf-8 -*-
"""
Created on Mon Oct 21 11:43:04 2019

@author: U117148
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt, lfilter, lfilter_zi, detrend

path = r"C:\Users\u117148\surfdrive\Beta\data\RESP\shouoldiintegrate.txt"#r"C:/Users/u117148/surfdrive/Beta/data/RESP/Bitalino/abele_zombies_spider_waist.txt"
data = np.loadtxt(path)

rawsignal = data[:, -1]

## real-time simulation of continuous filtering
nyq = 0.5 * 1000
#lowcut = 0.05 / nyq
highcut = 0.5 / nyq
b, a = butter(3, highcut, btype='lowpass')
zi = lfilter_zi(b, a)

#filtsignal = filtfilt(b, a, rawsignal, method='pad')
#derivedsignal = np.ediff1d(filtsignal, to_begin=0)

# apply leaky integrator (https://nl.mathworks.com/help/signal/examples/practical-introduction-to-digital-filtering.html)
#integratedoffline = filtfilt(1, [1, -0.999], rawsignal)

#meanraw = np.mean(rawsignal)
#recursive = np.zeros(rawsignal.size)
#for i in np.arange(1, rawsignal.size):
#  recursive[i] = recursive[i - 1] + rawsignal[i] - meanraw



#dcblock = np.zeros(rawsignal.size)
#for i in np.arange(1, rawsignal.size):
#  dcblock[i] = rawsignal[i] - rawsignal[i - 1] + 0.999 * dcblock[i - 1]




window = int(np.ceil(0.05 * 1000))
dcblocked = []
previous_dc = (np.zeros(window) - 1) * 400
previous_raw = np.zeros(window)
beg = 0
end = window

while end < len(rawsignal):
    
    
    raw = np.mean(rawsignal[beg:end])
    
    dc = raw - previous_raw + 0.999 * previous_dc
    
    dcfilt, zi = lfilter(b, a, dc, zi=zi)
    
    dcblocked.extend(dcfilt)
    

    previous_dc = dc
    previous_raw = raw
    
    beg += window
    end += window
  
  
#window_mean = int(np.ceil(20 * 1000))
#window_integral = int(np.ceil(0.1 * 1000))
#mean = 0
#integralonline = []
#previous = np.zeros(window_integral)
#beg = 0
#end = window_integral
#
#while end < len(rawsignal):
#    
#    if end >= window_mean:
#        mean = np.mean(rawsignal[end - window_mean:end])
#    
#    dat = rawsignal[beg:end]
#    
#    current = previous + np.mean(dat) - mean
#    
#    integralonline.extend(current)
#    
##    if end >= window_mean:
##        integralonline[end - window_mean:end] = detrend(integralonline[end - window_mean:end])
#
#    previous = current
#    
#    
#    beg += window_integral
#    end += window_integral
    
  
#zi = [0]
#window_size = int(np.ceil(0.1 * 1000))
#integratedonline = []
#beg = 0
#end = window_size
#while end < len(rawsignal):
#
#    dat = rawsignal[beg:end]
#    filt, zi = lfilter([1], [1, -0.999], dat, zi=zi)
#    integratedonline.extend(filt)
#    
#    beg += window_size
#    end += window_size
    



fig = plt.figure()
ax0 = fig.add_subplot(211)
ax0.plot(rawsignal)
ax0.plot(data[:, 1]*max(rawsignal), c='r', alpha=0.5)
ax0.axhline(y=400)
ax1 = fig.add_subplot(212, sharex=ax0)
ax1.plot(dcblocked)
ax1.plot(data[:, 1]*max(dcblocked), c='r', alpha=0.5)
ax1.axhline(y=0)





