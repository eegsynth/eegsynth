# Synchronization Module

The goal of this module is to use a continuous control value from the REDIS buffer for synchronization. The time between pulses scales linearly with the control value magnitude.

The regular output is sent as event to the REDIS buffer, as trigger to the serial CV/Gate hardware and as clock message to MIDI.

## Requirements

The rate should be expressed in beats per minute.
The REDIS buffer should be running.
The MIDI port and serial port will be opened when required.

## Software Requirements

Python 2.x
Redis package for Python
mido
