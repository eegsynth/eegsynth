# Frequently Asked Questions

## I receive a "Bad file descriptor" error

If openbci2ft gives this error trying to access /dev/ttyUSB0, it
is because the device is readonly for a normal user. The problem
does not apply if you run openbci2ft as root, i.e. with sudo.

## How can I improve the timing of the OpenBCI data stream

On http://ebrain.io/openbci-ftdi-driver/ and http://www.ftdichip.com/Support/Documents/AppNotes/AN232B-04_DataLatencyFlow.pdf
you can find suggestions to improve timing for the FTDI driver that is used with the OpenBCI RF dongle.
