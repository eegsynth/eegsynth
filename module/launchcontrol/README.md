LaunchControl module
====================

The purpose of this module is to process input MIDI commands from a Novation LaunchControlXL digital control surface. The values of the sliders and knobs are sent as control signals to the REDIS buffer. The button press and release events are sent as triggers to the REDIS buffer.

** Requirements **

The LaunchControlXL should be connected to an USB port.
The REDIS buffer should be running.

** Software Requirements **

portmidi
python 2.x
mido python library
redis python library
