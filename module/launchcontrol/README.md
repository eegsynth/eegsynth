LaunchControl module
====================

The goal of this module is to receive input MIDI commands from a LaunchControlXL. The values of the sliders and the buttons are sent as control signals to the REDIS buffer. The key press and release events are sent as triggers to the REDIS buffer.


** Requirements **

The LaunchControlXL should be connected to the USB port.
The REDIS buffer should be running.
