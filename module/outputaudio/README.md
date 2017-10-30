# Output Audio Module

The purpose of this module is to send a signal from a FieldTrip buffer to the audio card, i.e. to play the signal to the attached speakers or headset.

This module is based on a compiled applicatin that is implemented in C-code. The source code of the application itself is maintained in the FieldTrip project.

## Requirements

The FieldTrip buffer should be running and should receive one or two channels of data at at appropriate sampling rate (11025, 22050, or 44100 Hz).

The computer running this module should have a supported audio system.

## Software Requirements

The compiled binary can be downloaded with the eegsynth/bin/install script, or should be compiled in fieldtrip/realtime/src.
