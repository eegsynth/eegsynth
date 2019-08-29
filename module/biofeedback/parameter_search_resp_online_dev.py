# -*- coding: utf-8 -*-
"""
Created on Thu Aug 29 09:02:38 2019

@author: U117148
"""

import wfdb
from wfdb import processing
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from resp_online_dev import extrema_signal

records = wfdb.get_record_list('bidmc', records='all')

del_indices = [4, 26, 43]
#records = [records[i] for i in del_indices]
records = [i for j, i in enumerate(records) if j not in del_indices]

lrates = [None]#np.linspace(0.01, 0.5, 4)
promweights = np.linspace(0.1, 1, 4)

results = []

for lrate in lrates:
    
    for promweight in promweights:
        
#        print('lrate = {} and promweight = {}'.format(lrate, promweight))
        
        sensitivity1 = []
        sensitivity2 = []
        precision1 = []
        precision2 = []
        
        for record in records:
            
            print('processing record {}'.format(record))

            data = wfdb.rdrecord(record, pb_dir='bidmc')
            annotation = wfdb.rdann(record, pb_dir='bidmc', extension='breath')
        
            sfreq = data.fs
            resp_chan = data.sig_name.index('RESP,')
            resp = data.p_signal[:, resp_chan]
            annotators = annotation.aux_note
            # get the indices of each annotator's peaks (i gives index, j gives string)
            annotator1 = [i for i, j in enumerate(annotators) if j == 'ann1']
            annotator2 = [i for i, j in enumerate(annotators) if j == 'ann2']
            manupeaks1 = annotation.sample[annotator1]
            manupeaks2 = annotation.sample[annotator2]
            algopeaks = extrema_signal(resp, sfreq, promweight, lrate)
            
#            plt.figure()
#            plt.plot(resp)
#            plt.scatter(manupeaks1, resp[manupeaks1], c='m')
#            plt.scatter(manupeaks2, resp[manupeaks2], c='b')
#            plt.scatter(algopeaks, resp[algopeaks], c='g', marker='X', s=150)
            
             # unilateral extend of acceptance margin centered on each algopeak; in sec
            margin = 0.5
        
            comp1 = processing.compare_annotations(manupeaks1,
                                                   np.ravel(algopeaks),
                                                   int(margin * sfreq))
            tp1 = comp1.tp
            fp1 = comp1.fp
            fn1 = comp1.fn
            
            comp2 = processing.compare_annotations(manupeaks2,
                                                   np.ravel(algopeaks),
                                                   int(margin * sfreq))
            tp2 = comp1.tp
            fp2 = comp1.fp
            fn2 = comp1.fn
        
        
            # calculate two metrics for benchmarking (according to AAMI guidelines):
            # 1. sensitivity: how many of the manually annotated peaks does the
            # algorithm annotate as peaks (TP / TP + FN)?
            # 2. precision: out of all peaks that are algorithmically annotated as
            # peaks (TP + FP), how many are correct (TP)?
            sensitivity1.append(float(tp1) / (tp1 + fn1))
            precision1.append(float(tp1) / (tp1 + fp1))
            sensitivity2.append(float(tp2) / (tp2 + fn2))
            precision2.append(float(tp2) / (tp2 + fp2))
            
#            print(sensitivity1[-1], precision1[-1])
#            print(sensitivity2[-1], precision2[-1])
            
        
        sensitivity = np.mean((np.mean(sensitivity1), np.mean(sensitivity2)))
        precision = np.mean((np.mean(precision1), np.mean(precision2)))
        results.append([lrate, promweight, sensitivity, precision])
        print(results[-1])
        
results_df = pd.DataFrame(results, columns=['lrate', 'promweight',
                                            'sensitivity', 'precision'])
results_df.to_pickle(r'C:\Users\u117148\surfdrive\Beta\eegsynth\module\biofeedback\parameter_search_knuth_outliers_removed.pkl')
                