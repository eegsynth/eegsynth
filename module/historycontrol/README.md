# Historycontrol module

This module computes properties over the history of control channels from Redis, such as the median and the standard deviation, using a sliding window. These values are written back into the Redis buffer where they can be used by the postprocessing module to create smoothed or normalized control channels.
