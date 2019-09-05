#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  5 14:06:43 2019

@author: pi
"""

import numpy as np
import matplotlib.pyplot as plt
from filters import butter_lowpass_filter


def extrema_signal(signal, sfreq, enable_plot=False):
    
    # initiate plot
    if enable_plot is True:
        plt.figure()
        ax1 = plt.subplot(211)
        ax2 = plt.subplot(212, sharex=ax1)
    
    # initiate variables
    block = 0  
    lastpeak = 0
    allpeaks = []
    

    # set free parameters
    window_size = int(np.ceil(3 * sfreq))
    # amount of samples to shift the window on each iteration
    stride = np.ceil(0.5 * sfreq)
    lrate = 0.5

    
    # start real-time simulation
    while block * stride + window_size <= len(signal):
        block_idcs = np.arange(block * stride,
                               block * stride + window_size,
                               dtype = int)
        # plot data in seconds
        block_sec = block_idcs / sfreq
        
        x = signal[block_idcs]
        
        x -= np.mean(x)
            
        # find zero-crossings
        xgreater = x > 0
        zerox = np.where(np.bitwise_xor(xgreater[1:], xgreater[:-1]))[0]
        
        # plot signal
        if enable_plot is True:
            ax1.plot(block_sec, x, c='r')
            ax1.vlines(block_sec[zerox[-1]], ymin=[0] * window_size,
                       ymax=[1000] * window_size)

        block += 1
        
    ax1.axhline(0)