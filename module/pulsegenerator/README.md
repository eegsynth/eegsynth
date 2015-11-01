Pulse Generator
===============

The goal of this module is to read a continuous control value from the REDIS buffer and to make a regular pulse (trigger). The time between subsequent pulses scales linearly with the control value magnitude. The output pulse is written as a serial output command to the USB cv/gate converter. The control value should be expressed in beats per minute (bpm).


** Requirements **

The REDIS buffer should be running. The control values do not have to exist at the start of execution, as there is an initial default value.
The USB cv/gate converter should be connected to the USB port.
