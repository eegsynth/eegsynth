Keyboard module
===============

The purpose of this module is to receive input MIDI commands from a keyboard, e.g. a digital piano. The key press events are translated into a control value representing the pitch. The force with which the key is pressed is send as trigger. Both the control value and the trigger are send to the REDIS buffer. It is possible to filter on key presses and/or key releases.

## Requirements

The MIDI keyboard should be connected to the USB port.
The REDIS buffer should be running.

## Software Requirements

portmidi
Python 2.x
mido Python library
Redis Python library
