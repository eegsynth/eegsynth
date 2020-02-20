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
#from ecg_online_light import rpeaks
from ecg_online import rpeaks
#from ecg_offline import peaks_signal


records = glob.glob(r'C:\Users\JohnDoe\surfdrive\Beta\Data\ECG\mitdb\*.dat')
annotations = glob.glob(r'C:\Users\JohnDoe\surfdrive\Beta\Data\ECG\mitdb'
                        '\*.atr')

#np.random.seed(1)
#selection = np.random.choice(range(len(records)), 1, replace=False)
#selection = [4,6,8,9,18,19,22,23,24,26,28,29,36,37,40,42,43,44,46]

sampto = None#int(60. * 1 * 360)
sampfrom = 0#int(15. * 360)

sensitivity = []
precision = []
   
for subject in zip(records, annotations):

#for i in selection:
#      
#    subject = zip(records, annotations)[i]

    print('processing subject {}'.format(subject[1][-7:-4]))

    data = wfdb.rdrecord(subject[0][:-4], sampto=sampto)
    annotation = wfdb.rdann(subject[1][:-4], 'atr',
                            sampfrom=sampfrom,
                            sampto=sampto)

    sfreq = data.fs
    ecg = data.p_signal[:, 0]

    manupeaks = annotation.sample
    #algopeaks = peaks_signal(ecg, sfreq)
    algopeaks = rpeaks(ecg, sfreq)

    # tolerance for match between algorithmic and manual annotation (in sec)
    tolerance = 0.05
    comparitor = compare_annotations(manupeaks, algopeaks,
                                     int(np.rint(tolerance * sfreq)))
    tp = comparitor.tp
    fp = comparitor.fp
    fn = comparitor.fn

#    plt.figure()
#    plt.plot(ecg)
#    plt.plot(np.square(ecg))
#    plt.plot(np.abs(ecg))
#    plt.scatter(manupeaks, ecg[manupeaks], c='m')
#    plt.scatter(algopeaks, ecg[algopeaks], c='g', marker='X', s=150)

    sensitivity.append(float(tp) / (tp + fn))
    precision.append(float(tp) / (tp + fp))
    print(sensitivity[-1], precision[-1])

print(np.mean(sensitivity), np.mean(precision))
