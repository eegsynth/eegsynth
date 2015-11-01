Keyboard module
===============

The goal of this module is to receive input MIDI commands from a keyboard, e.g. a digital piano. The notes corresponding to the key presses on the keyboard are translated into a control value that represents pith. The control value is send to the REDIS buffer, along with a trigger (gate) that indicates the precise onset of the key press. Information about the force with which the key is pressed and about the release of the key is not transmitted.

** Requirements **

The MIDI keyboard should be connected to the USB port.
The REDIS buffer should be running.
