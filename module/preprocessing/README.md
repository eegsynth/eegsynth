Pre-processing module
=====================

The purpose of this module is to do pre-processing on the ExG data that is recorded. For each of the output channels you can specify a mathematical equation to compute a linear combination from the input channel data. The input data is read from one FieldTrip buffer. The resulting data is written to another FieldTrip buffer.

If you do not specify channel names in the input section of the *.ini file, the channel names will be determined from the header of the incoming FieldTrip buffer.

## Requirements

Two FieldTrip buffers should be running, one of them should receive ExG data.

## Software Requirements

Python 2.x
