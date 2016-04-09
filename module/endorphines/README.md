Endorphines
===========

The purpose of this module is to send control values from REDIS to the Endorphin.es Shuttle Control. The Shuttle Control is a MIDI to CV/Gate converter with 16 channels that can be controlled from -5 to +5 Volt.

![Endorphin.es Shuttle Control](./shuttle-control.jpg)

## Requirements

The REDIS buffer should be running.
The Shuttle Control module should be connected on the USB port.
The channels of the Shuttle Control should be configured as "Pitchwheel" and should use MIDI channel 1-16.

## Software Requirements

portmidi
Python 2.x
mido Python library
Redis Python library
