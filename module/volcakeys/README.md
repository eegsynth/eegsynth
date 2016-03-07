Volca Keys module
=================

The purpose of this module is to write control values and notes as MIDI commands to the Korg Volca Keys.

Setting the MIDI channel: While holding down the MEMORY button, turn on the Volca. Specify the channel and press the REC button.

** Requirements **

The REDIS buffer should be running.
The Volca Keys should be connected over MIDI.

** Software Requirements **

portmidi
python 2.x
mido python library
redis python library

[note]
; you can comment out those that should NOT be sent over MIDI


[control]
; you can comment out those that should NOT be sent over MIDI


[default]
