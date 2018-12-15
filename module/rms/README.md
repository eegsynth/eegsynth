# Muscle Processing Module

The goal of this module is to read one or multiple channels of bipolar EMG data from the FieldTrip buffer, to compute a sliding window RMS amplitude, to apply offset, scaling, clipping and to output the normalized control signal for each channel to the Redis buffer.

This module implements automatic gain control by tracking (over time) the maximal and minimal value and scaling the output within this range. While the module is running, the automatic gain control can be frozen, re-initialized or adjusted (increased or decreased) with key-presses.
