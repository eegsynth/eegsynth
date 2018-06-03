# EOG Processing Module

The goal of this module is to read EOG data from the FieldTrip buffer, to detect eye blinks and saccades and to send a trigger (gate) to the REDIS buffer.

## Requirements

The FieldTrip buffer should be running and should receive incoming data.
The REDIS buffer should be running.

## Software Requirements

Python 2.x
redis
nilearn
