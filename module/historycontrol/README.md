# Historycontrol Module

The purpose of this module is to compute control values that calculated properties over its history, such as the median and the standard deviation, using a sliding window. These values are written back into the Redis buffer where they can be used by the postprocessing module to create smoothed or normalized signals
