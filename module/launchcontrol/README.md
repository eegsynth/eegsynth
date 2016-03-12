LaunchControl module
====================

The purpose of this module is to process input MIDI commands from a Novation LaunchControlXL digital control surface. The values of the sliders and knobs are sent as control signals to the REDIS buffer. The button press and release events are sent as triggers to the REDIS buffer.

## Requirements

The LaunchControlXL should be connected to an USB port.
The REDIS buffer should be running.

## Software Requirements

portmidi
Python 2.x
mido Python library
Redis Python library

## MIDI assignment

The LaunchControlXL has three rows of 8 rotary dials each, 8 sliders, two rows with 8 buttons, and some buttons on the right side. Here I will sketch the outline of the main control elements with the *default* MIDI codes. The MIDI codes can be reassigned with the Novation LaunchControlXL Editor application.

```
(13) (14) (15) (16) (17) (18) (19) (20)
(29) (30) (31) (32) (33) (34) (35) (36)
(49) (50) (51) (52) (53) (54) (55) (56)
  -    -    -    -    -    -    -    -
  |    |    |    |    |    |    |    |
 77   78   79    80  81   82   83   84
  |    |    |    |    |    |    |    |
  -    -    -    -    -    -    -    -
[00] [00] [00] [00] [00] [00] [00] [00]
[00] [00] [00] [00] [00] [00] [00] [00]
```
