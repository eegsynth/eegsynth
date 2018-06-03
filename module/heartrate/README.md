# Heart Rate Module

The goal of this module is to read an ECG channel from the FieldTrip buffer and to detect the heart rate. The heart rate is written as a continuous control value to the REDIS buffer (expressed in beats per minute).

## Requirements

The FieldTrip buffer should be running and should receive incoming data.
The REDIS buffer should be running.

## Software Requirements

Python 2.x
redis
mne
