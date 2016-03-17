EMG processing module
=====================

The goal of this module is to read one or multiple channels of bipolar EMG data from the FieldTrip buffer, to compute a sliding window RMS amplitude, to apply offset, scaling, clipping and to output the normalized control signal for each channel to the REDIS buffer.

This module implements automatic gain control by tracking (over time) the maximal and minimal value and scaling the output within this range. While the module is running, the gain control can be re-initialized with a key-press.

## Requirements

The FieldTrip buffer should be running and should receive incoming data.
The REDIS buffer should be running.
