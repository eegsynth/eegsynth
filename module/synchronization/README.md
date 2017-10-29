# Synchronization Module

The goal of this module is to use a continuous control value from the REDIS buffer for synchronization. The time between pulses scales linearly with the control value magnitude.

The output pulse can be written as a trigger to the REDIS buffer, can be written as a gate to the serial CV/Gate hardware, and can be used to synchronize MIDI using clock messages.

## Requirements

The rate should be expressed in beats per minute.
The REDIS buffer should be running.
The MIDI port and serial port will be opened when required.

## Software Requirements

Python 2.x
Redis package for Python
mido
