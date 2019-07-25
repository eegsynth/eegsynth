# Historysignal module

This module computes properties over the history of signals from the FieldTrip buffer, such as the median and the standard deviation, using a sliding window. These values are written into the Redis buffer where they can be used e.g. for scaling of the signal later in the pipeline.

You can use this module to create an amplitude envelope of an ExG or audio signal. Alternatively, you can also use the [rms](../rms) module to create an amplitude envelope.
