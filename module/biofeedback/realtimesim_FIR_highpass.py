# -*- coding: utf-8 -*-
"""
Created on Wed Sep 18 09:49:50 2019

@author: John Doe
"""

import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import firwin, lfilter, lfilter_zi, lfiltic


plt.figure()
ax1 = plt.subplot(211)
ax2 = plt.subplot(212, sharex=ax1)

path = r'C:\Users\JohnDoe\surfdrive\Beta\data\RESP\Bitalino\abele_zombies_spider_chest.txt'
signal = np.loadtxt(path)[:, -1]

avg = []

ax1.plot(signal)

sfreq = 1000
nyquist = sfreq / 2
highpass = 0.01 / nyquist
order = 1001

# initiate variables
window_size = int(np.ceil(0.1 * sfreq))
beg = 0
end = window_size 

b = firwin(order, cutoff=highpass, window='nuttall', pass_zero=False)
a = np.ones(1)

b_iir = np.array([1., -1.])
a_iir = np.array([1, -1 * 0.95])
zi = lfilter_zi(b_iir, a_iir)

# start real-time simulation
while end <= len(signal):
    
    dat = signal[beg:end]

    # initialize filter
    if beg == 0:
        
        zi = lfiltic(b_iir, a_iir, dat)
    else:
        filt, zi = lfilter(b_iir, a=a_iir, x=dat, zi=zi)
    
        ax2.plot(np.arange(beg, end), filt)
            
        avg.append(np.mean(filt))
    
    beg += window_size
    end += window_size

print(np.mean(avg))