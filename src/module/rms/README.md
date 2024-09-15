# Root-Mean-Square module

This module reads one or multiple channels from the FieldTrip buffer and computes the sliding-window RMS value, which is written to the Redis buffer as control channel.

You can use this module to create an amplitude envelope of an ExG or audio signal. Alternatively, you can also use [historysignal](../historysignal) to create an amplitude envelope.
