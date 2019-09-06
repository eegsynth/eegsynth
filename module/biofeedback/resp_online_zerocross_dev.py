#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  5 14:06:43 2019

@author: pi
"""

import numpy as np
import matplotlib.pyplot as plt
from filters import butter_lowpass_filter
from scipy.signal import detrend


def extrema_signal(signal, sfreq, enable_plot=False):
    
    # initiate plot
    if enable_plot is True:
        plt.figure()
        ax1 = plt.subplot(211)
        ax2 = plt.subplot(212, sharex=ax1)
    
    

    # set free parameters
    window_size = int(np.ceil(5 * sfreq))
    # amount of samples to shift the window on each iteration
    stride = np.ceil(0.5 * sfreq)
    
    # initiate variables
    block = 0  
    state = 'wrc'
    maxbr = 100
    micsfact = 0.5
    mdcsfact = 0.1
    ics = np.nan
    dcs = np.nan
    mics = micsfact * 60/maxbr
    mdcs = mdcsfact * 60/maxbr
    currentmin = -np.inf
    currentmax = np.inf
    lastrisex = -np.inf
    lastfallx = -np.inf

    
    # start real-time simulation
    while block * stride + window_size <= len(signal):
        block_idcs = np.arange(block * stride,
                               block * stride + window_size,
                               dtype = int)
        # plot data in seconds
        block_sec = block_idcs / sfreq
        
        dat = signal[block_idcs]
        # demean data
        dat = detrend(dat, type='constant')
        # plot signal
        if enable_plot is True:
            ax1.plot(block_sec, dat, c='r')
            
            
        # find zero-crossings
        greater = dat >= 0
        smaller = dat < 0
        
        if state == 'wrc':
        
            # search for rising crossing
            risex = np.where(np.bitwise_and(greater[1:], smaller[:-1]))[0]
            if risex.size > 0:
                risex = risex[-1]
                risex_idx = block_idcs[risex]
                if np.logical_and(risex_idx > lastrisex,
                                  risex_idx > lastfallx):
    
                    lastrisex = risex_idx
                    # update the current maximum
                    currentmax = np.max(dat[risex:])
                    # switch state
                    state = 'wfc'
                    
                    if enable_plot is True:
                        ax1.axvline(block_sec[risex], ymin=-250, ymax=250,
                                    colors='g')
                    
                    block += 1
                else:
                    # if no rising crossing has been found, update current minimum
                    currentmin = np.min(dat)
                    block += 1
            else:
                # if no rising crossing has been found, update current minimum
                currentmin = np.min(dat)
                block += 1
                
        elif state == 'wfc':
        
            # search for falling crossing
            fallx = np.where(np.bitwise_and(smaller[1:], greater[:-1]))[0]
            if fallx.size > 0:
                fallx = fallx[-1]
                fallx_idx = block_idcs[fallx]
                if np.logical_and(fallx_idx > lastrisex,
                                  fallx_idx > lastfallx):
                    lastfallx = fallx_idx
                    # update the current minimum
                    currentmin = np.min(dat[fallx:])
                    # switch state
                    state = 'wrc'
                    
                    if enable_plot is True:
                        ax1.axvline(block_sec[fallx], ymin=-250, ymax=250,
                                    colors='b')
                    
                    block += 1
                else:
                    currentmax = np.max(dat)
                    block += 1
            else:
                currentmax = np.max(dat)
                block += 1
        
    ax1.axhline(0)