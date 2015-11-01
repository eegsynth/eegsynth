EMG processing module
=====================

The goal of this module is to read one or multiple channels of bipolar EMG data from the FieldTrip buffer, to compute a sliding window RMS amplitude, to apply offset, scaling, clipping and to output the normalized control signal for each channel to the REDIS buffer.


** Requirements **

The FieldTrip buffer should be running and should receive incoming data.
The REDIS buffer should be running.
