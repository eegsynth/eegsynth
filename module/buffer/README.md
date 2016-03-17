FieldTrip buffer module
=======================

The goal of this module is to control the FieldTrip buffer. This buffer acts as a network transparent store for one or multiple channels of ExG data which are all sampled from the same acquisition device with the same sampling rate. The data is represented as a Nchannels*Ntimepoints matrix in a ring buffer. Furthermore, header information about the data stream is represented.

## Requirements

None.
