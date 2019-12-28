# Complexity module

This module reads EEG data from the FieldTrip buffer, average the channels to reduce computation time and computes a few complexity metrics using [NeuroKit](https://github.com/neuropsychology/NeuroKit.py). Finally, the results are written in Redis under the name of each metric. 
