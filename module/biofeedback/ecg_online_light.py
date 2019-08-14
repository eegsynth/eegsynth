# -*- coding: utf-8 -*-
"""
Created on Fri Mar  8 21:00:44 2019

@author: John Doe
"""

import numpy as np
import matplotlib.pyplot as plt

def rpeaks(signal, sfreq):
            
    # set free parameters
    # in samples; sufficiently small such that no two R-peaks can occur in the
    # same window
    window_size = np.ceil(0.3 * sfreq)
    # amount of samples the window is shifted on each iteration
    stride = np.ceil(0.05 * sfreq)
    # weight for R-peak threshold for post-training phase  
    pmax_weight = 0.7
    pmax_weight_train = 0.6
    # duration training in seconds
    dur_train = 15
    lrate_pmax = 0.2
    lrate_paid = 0.2
    
    # initiate stuff
    training_data = np.zeros([2, 1])
    block = 0
    signal = np.ravel(signal)
    
    while block * stride + window_size <= len(signal):
                
        block_idcs = np.arange(block * stride, block * stride + window_size,
                               dtype = int)

        x = signal[block_idcs]
        first_diff = x[1:] - x[:-1]
        inflect = inflection_nonzero(first_diff)
                
        # first row: voltage, second row: index (timestamp), '+1' makes the
        # inflection point coincide with the actual peak, since
        # 'inflection_nonzero()' returns the index -1 to the actual peak
        candidateR = np.stack((np.abs(x[inflect + 1] - np.mean(x)),
                               block_idcs[inflect + 1]))
    
        if candidateR.shape[1] > 0:
        
            # training
            if block_idcs[-1] <= dur_train * sfreq:
       
                # add only fresh data to training data; accumulate all training
                # data
                new_data = candidateR[1, :] > training_data[1, -1]
                training_data = np.column_stack((training_data,
                                                 candidateR[:, new_data]))
                
                # select only those peaks that exceed the amplitude threshold
                pmax_train = pmax_weight_train * np.max(training_data[0, :])
                above_pmax = training_data[0, :] > pmax_train
                first_pass = training_data[:, above_pmax]
                
                # select only those peaks that have a minimum distance of 200
                # msec to the previous peak
                peak_diff = np.abs(np.diff(first_pass[1, :]))
                above_paid = np.where(peak_diff > 0.2 * sfreq)[0]
                second_pass = first_pass[:, above_paid]
                
                # calculate initial threshold values
                pmax = np.mean(second_pass[0, :])
                paid = np.median(np.diff(second_pass[1, :]))
                
                # catch unrealistic values caused by noisy training data:
                # declare 65 bpm if paid indicates less than 40bpm or more 
                # than 200bpm
                if (paid < 0.67 * sfreq) or (paid > 0.3 * sfreq):
                    paid = 0.92 * sfreq
                
                if second_pass.size > 0:
                    # initiate Rpeaks for first post-training window
                    Rpeaks = second_pass[:, -1].reshape(-1, 1)
            
            # post-training
            else:
                
                # retain only candidate peaks that follow the last detected
                # peak by a minimum of 200 msec
                sieve_a = sieving(candidateR,
                                  'right',
                                  Rpeaks[1, -1],
                                  0.2 * sfreq)
               
                if sieve_a.shape[1] == 0:
                    
                    block += 1
                    continue
                
                elif sieve_a.shape[1] > 0:
                    
                    # retain only candidate peaks that are above threshold
                    pmaxR = sieve_a[:, sieve_a[0,:] >= pmax * pmax_weight]
                
                    if pmaxR.shape[1] == 0:
   
                        block += 1
                        continue
                        
                    elif pmaxR.shape[1] == 1:
                        Rpeaks = np.column_stack([Rpeaks, pmaxR])
                    
                    elif pmaxR.shape[1] >= 1: 
        
                        # give first priority to canidate peaks that are within
                        # -/+ 0.1 * paid of last detected peak + paid
                        sieve_b = sieving(pmaxR,
                                          'both',
                                          Rpeaks[1, -1] + paid,
                                          0.1 * paid)
                        
                        if sieve_b.shape[1] > 0:
                            pmaxR = sieve_b[:,sieve_b[0, :].argmax()]
                            Rpeaks = np.column_stack([Rpeaks, pmaxR])
                        # if no peaks are found, extend the sieve range
                        else:
                            
                            # give second priority to canidate peaks that are
                            # within -/+ 0.2 * paid of last detected peak +
                            # paid
                            sieve_c = sieving(pmaxR,
                                              'both',
                                              Rpeaks[1, -1] + paid,
                                              0.2 * paid)
                        
                            if sieve_c.shape[1] > 0:
                                pmaxR = sieve_c[:,sieve_c[0, :].argmax()]
                                Rpeaks = np.column_stack([Rpeaks, pmaxR])
                            else:    
                            
                                # give third priority to candidate peaks that
                                # are within -/+ 0.3 * paid of last detected
                                # peak + paid
                                sieve_d = sieving(pmaxR,
                                                  'both',
                                                  Rpeaks[1, -1] + paid,
                                                  0.3 * paid)
                        
                                if sieve_d.shape[1] > 0:
                                    pmaxR = sieve_d[:,sieve_d[0, :].argmax()]
                                    Rpeaks = np.column_stack([Rpeaks, pmaxR])
                                else:
                                    # ignore segment
                                    
                                    block += 1
                                    continue
                                    
                # update threshold
                paid = ((1 - lrate_paid) * paid + lrate_paid *
                        np.abs(np.diff(Rpeaks[1, -2:])))
                pmax = (1 - lrate_pmax) * pmax  + lrate_pmax * Rpeaks[0, -1]
            
            
            block += 1
            
        else:
            
            block += 1
            continue
   
    return np.asarray(Rpeaks[1, 1:]).astype(int)


def inflection_nonzero(signal):
        pos = signal > 0    # disregard indices where slope equals zero
        npos = ~pos
        return ((pos[:-1] & npos[1:]) | (npos[:-1] & pos[1:])).nonzero()[0]
    
    
def sieving(signal, direction, center, extend):
    # direction: search to only right side of center ('right'), or search
    # on both sides of the center ('both')
    # center: center of search range
    # extend: extend of search range (unilaterally), expressed as fraction 
    # of paid
    
    sieve_range_pos = np.int(np.ceil(center + extend))
    sieve_range_neg = np.int(np.ceil(center - extend))
    
    if direction == 'right':
        candidate = signal[:,[i for i, element in enumerate(signal[1,:])
                        if element > sieve_range_pos]]
         
    elif direction == 'both':
        candidate = signal[:,[i for i, element in enumerate(signal[1,:])
                        if sieve_range_neg <= element <= sieve_range_pos]]
                
    return candidate
