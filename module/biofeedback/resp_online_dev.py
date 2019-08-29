# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import numpy as np
import matplotlib.pyplot as plt
from filters import butter_lowpass_filter
from scipy.signal import argrelextrema, peak_prominences


def extrema_signal(signal, sfreq, enable_plot=False):
    '''
    the goal is to provide a real-time estimates of breathing rate, based on
    the inhalation peaks; peaks are chosen over troughs since the former are
    more sharply defined than troughs in signals acquired with the Bitalino
    belt (link)
    
    detection is based on online averages of...
    
    ... breathing rate: throw out extrema that follow another extreme by
        half the period of the average rate
    ... peak prominence (link) : throw out extrema that have a prominen smaller
        than weight * average prominence
        
    update online average according to D. Knuth; https://dsp.stackexchange.com/
    questions/811/determining-the-mean-and-standard-deviation-in-real-time
    
    the algorithm can be run as a real-time simulation like so
    (enable_plot=True for visual introspection):
    
    from resp_online_dev import extrema_signal
    import numpy as np

    path = 
    channel = 
    sfreq =
    data = np.loadtxt(path)[channel]
    extrema_signal(data, sfreq, enable_plot=True)

    '''
  
    # enforce numpy and vector-form
    signal = np.ravel(signal)

    # set free parameters
    window_size = int(np.ceil(3 * sfreq))
    # amount of samples to shift the window on each iteration
    stride = np.ceil(0.5 * sfreq)
    promweight = 1#promweight

    # initiate variables
    block = 0  
#    avgprom = np.nan
    avgprom_lrate = np.nan
    lastpeak = 0
    lrate = 0.1
    allpeaks = []
    
    # initiate plot
    if enable_plot is True:
        plt.figure()
        ax1 = plt.subplot(211)
        ax2 = plt.subplot(212, sharex=ax1)
    
    # simulate online filtering (later done by preprocessing module); filter
    # out fluctuations that occur faster than 0.5 Hz (breathing rate faster
    # than 30)
    signal = butter_lowpass_filter(signal, 0.5, sfreq)
    
    # start real-time simulation
    while block * stride + window_size <= len(signal):
        block_idcs = np.arange(block * stride,
                               block * stride + window_size,
                               dtype = int)
        # plot data in seconds
        block_sec = block_idcs / sfreq
        
        x = signal[block_idcs]
        
        # plot signal
        if enable_plot is True:
            ax1.plot(block_sec, x, c='r')
        
        # identify peaks
        peaks = argrelextrema(x, np.greater)[0]
        
        # if no peak was detected jump to the next block 
        if peaks.size < 1:
            block += 1
            continue
        
        # index of peak relative to block and absolute to recording
        peakidx = peaks[-1]
        peak = block_idcs[peakidx]
            
        # if no new peak was detected jump to next block
        if peak <= lastpeak:
            block += 1
            continue
        
        # plot new peak
        if enable_plot is True:
            ax1.scatter(block_sec[peakidx], x[peakidx], c='y', marker='P',
                        s=200)
        
        # determine rate and prominence
        rate = (60 / ((peak - lastpeak) / sfreq))
        prom = peak_prominences(x, [peakidx])[0]
        
        # initiate averages on first block
        if np.isnan(avgprom_lrate):
#            avgprom = prom
            avgprom_lrate = prom
        
        # update averages
#        avgprom = (avgprom + (prom - avgprom) / (block + 1))
        avgprom_lrate  = (1 - lrate) * avgprom_lrate  + lrate * prom
        
        if enable_plot is True:
            ax2.plot(block_sec, np.ones(window_size) * avgprom_lrate, c='b')
#            ax2.plot(block_sec, np.ones(window_size) * avgprom, c='g')
               
        # evaluate peak validity
        if (rate <= 30) & (prom > promweight * avgprom_lrate):

            allpeaks.append(peak)
            lastpeak = peak
        
            # plot peaks that made it past the thresholds
            if enable_plot is True:
                ax1.scatter(block_sec[peakidx], x[peakidx], c='m', marker='X', 
                            s=200)
            
        block += 1
    
    return allpeaks
        