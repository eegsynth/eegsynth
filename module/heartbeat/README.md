Heartbeat
=========

The goal of this module is to read ECG data from the FieldTrip buffer, to detect the heartbeat by thresholding the QRS and  to send a trigger (gate) to the REDIS buffer.


** Requirements **

The FieldTrip buffer should be running and should receive incoming data.
The REDIS buffer should be running.
