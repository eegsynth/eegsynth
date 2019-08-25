# -*- coding: utf-8 -*-
"""
Created on Wed Feb 27 14:24:54 2019

@author: John Doe
"""

import wfdb
from wfdb import processing
import matplotlib.pyplot as plt
import numpy as np
from resp_online_dev import extrema_signal

records = wfdb.get_record_list('bidmc', records='all')
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
#    algopeaks, _, _, _ = extrema_signal(resp, sfreq)
    algopeaks = extrema_signal(resp, sfreq)

    plt.figure()
    plt.plot(resp)
    plt.scatter(manupeaks1, resp[manupeaks1], c='m')
    plt.scatter(manupeaks2, resp[manupeaks2], c='b')
    plt.scatter(algopeaks, resp[algopeaks], c='g', marker='X', s=150)

    # perform benchmarking against each annotator seperately; an
    # algorythmically annotated peaks is scored as true positives if it is
    # within 700 msec of a manually annotated peak, this relatively large
    # window was chosen to account for the clipping that occurs in many of the
    # recordings; clipping results in large palteaus that make placement of
    # peak somewhat arbitrary (algorithm places peak at the edges while manual
    # annotation places peak towards the middle); for non-clipped peaks, the
    # agreement of manual and algorithmic annotation is within a range smaller
    # than 700 msec (enable plotting to confirm)

    # unilateral extend of acceptance margin centered on each algopeak; in sec
    acceptance_margin = 0.5

    comparitor1 = processing.compare_annotations(manupeaks1,
                                                 np.ravel(algopeaks),
                                                 int(acceptance_margin *
                                                     sfreq))
    tp1 = comparitor1.tp
    fp1 = comparitor1.fp
    fn1 = comparitor1.fn

    comparitor2 = processing.compare_annotations(manupeaks2,
                                                 np.ravel(algopeaks),
                                                 int(acceptance_margin *
                                                     sfreq))
    tp2 = comparitor2.tp
    fp2 = comparitor2.fp
    fn2 = comparitor2.fn

    # calculate two metrics for benchmarking (according to AAMI guidelines):
    # 1. sensitivity: how many of the manually annotated peaks does the
    # algorithm annotate as peaks (TP / TP + FN)?
    # 2. precision: out of all peaks that are algorithmically annotated as
    # peaks (TP + FP), how many are correct (TP)?
    sensitivity1.append(float(tp1) / (tp1 + fn1))
    precision1.append(float(tp1) / (tp1 + fp1))
    sensitivity2.append(float(tp2) / (tp2 + fn2))
    precision2.append(float(tp2) / (tp2 + fp2))
    print(sensitivity1[-1], precision1[-1])
    print(sensitivity2[-1], precision2[-1])

print(np.mean(sensitivity1), np.mean(precision1))
print(np.mean(sensitivity2), np.mean(precision2))
