# Pre-processing Module

The purpose of this module is to do filtering and re-referencing on the ExG data that is recorded.  The input data is read from one FieldTrip buffer. The resulting data is written to another FieldTrip buffer.

If you do not specify channel names in the input section of the *.ini file, the channel names will be determined from the header of the incoming FieldTrip buffer.

## Requirements

Two FieldTrip buffers should be running: one of them should be receiving ExG data, the other will receive the output data from this module.

## Software Requirements

Python 2.x
scipi
