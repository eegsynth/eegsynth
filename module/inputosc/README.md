Input OSC module
================

The purpose of this module is to process input messages that are received from Open Sound Control (OSC). The values of the OSC messages are send as control signals to the REDIS buffer. The button press and release events are sent as triggers to the REDIS buffer.

** Requirements **

The REDIS buffer should be running.
The receiving OSC server address and port should be configured.

** Software Requirements **

Python 2.x
Redis Python library
pyosc Python library
