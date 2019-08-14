# -*- coding: utf-8 -*-
"""
Created on Tue Mar 5 10:14:36 2019

@author: U117148
"""

import numpy as np
from filters import butter_bandpass_filter
import matplotlib.pyplot as plt

def rpeaks(signal, sfreq, enable_plot=False):

    if enable_plot is True:
        plt.figure()
    
    # enforce numpy and vector-form
    signal = np.ravel(signal)

    # set free parameters
    window_size = np.ceil(3 * sfreq)
    # amount of samples to shift the window on each iteration
    stride = np.ceil(0.5 * sfreq)
    # minimal time bewteen beats
    min_ibi = 0.2 * sfreq
    
    # kernel lengths for moving averages
    w1 = int(np.ceil(0.096 * sfreq))
    w2 = int(np.ceil(0.61 * sfreq))
    # threshold parameter
    beta = 0.08
    
    # initiate stuff
    block = 0
    peaks = []
    prev_peak = np.nan
    last_peak = np.nan


    while block * stride + window_size <= len(signal):
        block_idcs = np.arange(block * stride, block * stride + window_size, 
                                  dtype = int)
        
        # amplify QRS complexes
        x = signal[block_idcs]
        filt = butter_bandpass_filter(x, 8., 20., 360, order=2)
        sqrd = filt**2
        
        # filter with moving averages
        ma1 = moving_average(sqrd, w1)
        ma2 = moving_average(sqrd, w2)
        
        # calculate threshold for R peaks detection
        z = np.mean(sqrd)
        alpha = ma2 + beta * z 
        amp_thresh = ma2 + alpha
             
        if enable_plot is True:
#            plt.axvline(block_idcs[0], color='g')
#            plt.axvline(block_idcs[-1], color='r')
            plt.plot(block_idcs, x, c='b')
            plt.plot(block_idcs, sqrd)
            plt.plot(block_idcs, ma1, c='m')
            plt.plot(block_idcs, amp_thresh, c='g')
            
        # find QRS complexes
        QRS_idcs = np.where(ma1 > amp_thresh)[0]
        if QRS_idcs.size > 0:
#            if enable_plot is True:
#                plt.scatter(block_idcs[QRS_idcs], np.ones(QRS_idcs.size))

            QRS_edges = np.where(np.diff(QRS_idcs) > 1)[0]
            # add start of first QRS and end of last QRS complex
            QRS_edges = np.concatenate(([0],
                                        QRS_edges + 1,
                                        [QRS_idcs.size-1]))
            # for each QRS...
            for i in zip(QRS_edges[0:], QRS_edges[1:]):
                beg_QRS = QRS_idcs[i[0]]
                end_QRS = QRS_idcs[i[1]-1]
                
                # ... check if the QRS complex has the minimally required
                # duration...
                if (end_QRS - beg_QRS) >= w1:

                    #... and find R peaks within QRS complexes (only retain
                    # last beat once enclosing for-loop ends)
                    
                    # narrow down search range for R peak by first identifying
                    # the local maxiumum in the filtered signal
                    filt_peak = np.argmax(np.abs(filt[beg_QRS:end_QRS]))
                    last_peak = block_idcs[0] + beg_QRS + filt_peak

#                    if enable_plot is True:
#                        plt.axvspan(block_idcs[beg_QRS], block_idcs[end_QRS],
#                                    alpha=0.25)

            # the first beat has not been detected yet
            if np.isnan(prev_peak) and np.isnan(last_peak):
                block += 1
                continue
            elif np.isnan(prev_peak):
                prev_peak = last_peak
                block += 1
                continue

            # require a minimum time between beats
            if last_peak - prev_peak > min_ibi:
                peaks.append(last_peak)
                prev_peak = last_peak

        block += 1
    
    if enable_plot is True:
        plt.scatter(peaks, signal[peaks], c='r')
    return np.asarray(peaks).astype(int)


def moving_average(signal, window_size):
    
    return np.convolve(signal, np.ones((window_size,))/window_size,
                       mode='same') 
