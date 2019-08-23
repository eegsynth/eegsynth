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
    path = 
    channel = 
    sfreq
    data = np.loadtxt(path)[channel]
    extrema_signal(data, sfreq, enable_plot=True)

    '''
  
    # enforce numpy and vector-form
    signal = np.ravel(signal)
    sfreq = 1000

    # set free parameters
    window_size = int(np.ceil(3 * sfreq))
    # amount of samples to shift the window on each iteration
    stride = np.ceil(0.5 * sfreq)
    promweight = 0.4

    # initiate variables
    block = 0  
    avgrate = 15
    avgprom = 0
    lastpeak = 0
    validblocks = 0
    
    # initiate plot
    if enable_plot is True:
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
        if peak - lastpeak == 0:
            block += 1
            continue
        
        # plot new peak
        if enable_plot is True:
            ax1.scatter(block_sec[peakidx], x[peakidx], c='y', marker='P',
                        s=200)
        
        # if current peak occurs too close to last peak jump to next block
        rate = (60 / ((peak - lastpeak) / sfreq))
        if rate > 2 * avgrate:
            block += 1
            continue
        
        # plot peaks that made it past the rate threshold
        if enable_plot is True:
            ax1.scatter(block_sec[peakidx], x[peakidx], c='g', marker='X', 
                        s=200)
        
        # determine the prominence of each peak
        prom = peak_prominences(x, [peakidx])[0]
        # if current peak prominence is too small, jump to next block; larger
        # promweight is more conservative (throws out more peaks)      
        if prom < avgprom * promweight:
            block += 1
            continue
        
        # update average parameters
        avgprom = (avgprom + (prom - avgprom) / (validblocks + 1))
        avgrate = (avgrate + (rate - avgrate) / (validblocks + 1))
        lastpeak = peak
        # for the real-time averages it is important to keep a counter of only
        # the valid blocks (blocks on which peak made it past both thresholds)
        validblocks += 1
        
        # plot average parameters and peaks that made it past the prominence
        # threshold
        if enable_plot is True:
            ax1.scatter(block_sec[peakidx], x[peakidx], c='m', marker='X', 
                        s=200)
            ax2.plot(block_sec, np.ones(window_size) * avgrate, c='b')
            ax2.plot(block_sec, np.ones(window_size) * avgprom, c='g')
            
        block += 1
        