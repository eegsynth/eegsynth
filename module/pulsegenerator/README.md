Pulse Generator Module
======================

The goal of this module is to read a continuous control value from the REDIS buffer and send regular pulses. The time between pulses scales linearly with the control value magnitude. The output pulse is written as a trigger to the REDIS buffer.

## Requirements

The control values do not have to exist at the start of execution, as there are initial default values.
The rate should be expressed in beats per minute.
The REDIS buffer should be running.

## Software Requirements

Python 2.x
Redis package for Python
