# Pre-processing Module

The purpose of this module is to do filtering and re-referencing on the ExG data that is recorded.  The input data is read from one FieldTrip buffer. The resulting data is written to another FieldTrip buffer.

If you do not specify channel names in the input section of the .ini file, the channel names will be determined from the header of the incoming FieldTrip buffer.

## Incompatible settings

Not all preprocessing options are computationally possible.

If you get the error `ValueError: The length of the input vector x must be at least padlen, which is XX`, you should increase the window length.
