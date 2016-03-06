Input OSC module
================

The purpose of this module is to process input Open Sound Control (OSC) messages. The values of the OSC messages are send as control signals to the REDIS buffer. The button press and release events are sent as triggers to the REDIS buffer.

** Requirements **

The REDIS buffer should be running.

** Software Requirements **

python 2.x
redis python library
pyosc
