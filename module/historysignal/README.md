# Historysignal module

The purpose of this module is to compute control values that calculated properties over the
signal history, such as the median and the standard deviation, using a sliding window. These
values are written into the Redis buffer where they can be used by for scaling of the signal
later in the pipeline.
