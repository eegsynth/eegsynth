# -*- coding: utf-8 -*-
"""
Created on Wed Feb 27 14:24:54 2019

@author: John Doe
"""

import wfdb
from wfdb.processing import compare_annotations
import glob
import matplotlib.pyplot as plt
import numpy as np
#from ecg_online import rpeaks
from rreader import rpeaks
#from heartrate_eegsynth import rpeaks

records = glob.glob(r'C:\Users\John Doe\surfdrive\Beta\Data\ECG\mitdb\*.dat')
annotations = glob.glob(r'C:\Users\John Doe\surfdrive\Beta\Data\ECG\mitdb'
                        '\*.atr')

sampto = int(60. * 10 * 360)#'end'
sampfrom = 0#int(15. * 360)

selection = [2, 4, 6, 8, 15, 18, 23, 24, 26, 28, 40, 41, 42, 44]

window_sizes = [0.3, 0.4, 0.5]
strides = [0.05, 0.1, 0.15]
pmax_weights = [0.7]
lrates_pmax = [0.2]
lrates_paid = [0.2]

means = []

for window_size in window_sizes:
    
    for stride in strides:
    
        for pmax_weight in pmax_weights:
                        
            for lrate_pmax in lrates_pmax:
                
                for lrate_paid in lrates_paid:
        
                    sensitivity = []
                    precision = []
                            
    #                    for subject in zip(records, annotations):
                       
                    for i in selection:
                                
                        subject = zip(records, annotations)[i]
                                
    #                        print 'processing subject ' + subject[1][-7:-4]
                    
                        data = wfdb.rdrecord(subject[0][:-4], sampto=sampto)
                        annotation = wfdb.rdann(subject[1][:-4], 'atr',
                                                sampfrom=sampfrom,
                                                sampto=sampto)
                    
                        sfreq = data.fs
                        ecg = data.p_signal[:, 0]
                    
                        manupeaks = annotation.sample
                        algopeaks = rpeaks(ecg,
                                           sfreq,
                                           window_size,
                                           stride,
                                           pmax_weight,
                                           lrate_pmax,
                                           lrate_paid)
                            
                        # tolerance for match between algorithmic and manual annotation (in sec)
                        tolerance = 0.05    
                        comparitor = compare_annotations(manupeaks, algopeaks,
                                                         int(tolerance * sfreq))
                        tp = comparitor.tp
                        fp = comparitor.fp
                        fn = comparitor.fn
                    
                    #    plt.figure()
                    #    plt.plot(ecg)
                    #    plt.scatter(training_peaks, ecg[training_peaks], c='0')
                    #    plt.scatter(manupeaks, ecg[manupeaks], c='m')
                    #    plt.scatter(algopeaks, ecg[algopeaks], c='g', marker='X', s=150)
                    
                        sensitivity.append(float(tp) / (tp + fn))
                        precision.append(float(tp) / (tp + fp))
    #                        print sensitivity[-1], precision[-1]
                        
                    means.append((np.mean(sensitivity), np.mean(precision)))
                        
                    print 'window size =', window_size, 'stride =', stride, 'pmax_weight =', pmax_weight, 'lrate_pmax=', lrate_pmax, 'lrate_paid=', lrate_paid, (np.mean(sensitivity), np.mean(precision))
                    
    #                    print np.mean(sensitivity), np.mean(precision)
