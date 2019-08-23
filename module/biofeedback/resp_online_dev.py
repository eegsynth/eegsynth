# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import numpy as np
import matplotlib.pyplot as plt
from filters import butter_lowpass_filter


def extrema_signal(signal, sfreq, enable_plot=False):
    '''
    the goal is to provide real-time estimates of a) breathing rate, and b)
    the current phase of breathing (inspiration, expiration); a is
    estimated based on negative zero-crossings of the signal's gradient (i.e.,
    one breathing cycle is defined as peak-to-peak difference, since peaks are
    more sharply defined than troughs with the Bitalino belt []); b) is simply
    the gradient of the signal at any time
    
    path = 
    channel = 
    data = np.loadtxt(path)[:, channel]
    extrema_signal(data, 1000, enable_plot=True)
    
    online average of...
    
    ... breathing frequency: throw out extrema that follow another extreme by
        half the period of that average frequency
    ... amplitude difference: throw out extrema that have a difference smaller
        than weight * average amplitude difference from the preceding extrema

    '''

  
    # enforce numpy and vector-form
    signal = np.ravel(signal)
    sfreq = 1000

    # set free parameters
    window_size = np.ceil(3 * sfreq)
    # amount of samples to shift the window on each iteration
    stride = np.ceil(1 * sfreq)
    extend = int(np.ceil(0.2 * sfreq))

    # initiate stuff
    block = 0
    last_extreme = 0
    gradthresh = 0    
    peaks = []
    
    # simulate online filtering (later done by preprocessing module);
    # filter out fluctuations that occur faster than 0.5 Hz (breathing
    # rate faster than 30)
    signal = butter_lowpass_filter(signal, 0.5, sfreq)
    
    
    if enable_plot is True:
        ax1 = plt.subplot(211)
        ax2 = plt.subplot(212, sharex=ax1)
        # plot line to visualize zero crossing
        ax2.axhline(y = 0)
        

    while block * stride + window_size <= len(signal):
        block_idcs = np.arange(block * stride,
                               block * stride + window_size,
                               dtype = int)
        # plot data in seconds
        block_sec = block_idcs / sfreq
        
        x = signal[block_idcs]
        grad = np.gradient(x)
        
        if enable_plot is True:
            ax1.plot(block_sec, x, c='r')
            ax2.plot(block_sec, grad)
        
        # get negative zero crossings
        extrema = neg_crossings(grad)
                    
        if extrema.size > 0:
            extreme = extrema[-1]
            horzdiff = block_idcs[extreme] - last_extreme
            if enable_plot is True:
                ax1.scatter(block_sec[extreme], x[extreme], c='y', marker='P',
                            s=200)
            # get average gradient in 200msec preceding each negative zero
            # crossing
            if grad[extreme - extend:extreme].size > 0:
                avggrad = np.average(grad[extreme - extend:extreme])
                # if the current temporal difference exceeds a second, consider
                # the current zero crossing a valid extreme; also the average 
                # gradient preceding the extreme must exceeed a threshold
                if (horzdiff > 1 * sfreq) and (avggrad > 0.3 * gradthresh):
                    # update running mean of gradient threshold (Knuth; 
                    # https://dsp.stackexchange.com/questions/811/determining-
                    # the-mean-and-standard-deviation-in-real-time)
                    gradthresh = (gradthresh + (avggrad - gradthresh) /
                                  (block + 1))
                    peaks.append(block_idcs[extreme])
                    if enable_plot is True:
                        ax1.scatter(block_sec[extreme], x[extreme], c='m',
                                    marker='X', s=200)

            if peaks:
                last_extreme = peaks[-1]

        block += 1
        
    return peaks

def neg_crossings(signal):
        pos = signal > 0
        return (pos[:-1] & ~pos[1:]).nonzero()[0]