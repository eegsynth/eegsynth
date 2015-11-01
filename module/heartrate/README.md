FieldTrip buffer
================

The goal of this module is to read ECG data from the FieldTrip buffer, to detect the heart rate and to write this as a control signal to the REDIS buffer. The heart rate is expressed in beats per minute (bpm).


** Requirements **

The FieldTrip buffer should be running and should receive incoming data.
The REDIS buffer should be running.
