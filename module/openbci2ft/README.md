# OpenBCI Module

The goal of this module is to read data from the OpenBCI board (over the Bluetooth RF interface) and to write this data to the FieldTrip buffer. At the start of data acquisition the FieldTrip buffer will be reset.

![OpenBCI](./openbci.jpg)

Prior to starting this module the FieldTrip buffer should be running, the RF dongle should be plugged and the board should be switched on.

Furthermore, you should have write permissions to the device. If *getattr error* is shown this is likely not the case. In that case one can run the openbci2ft module in sudo mode.
