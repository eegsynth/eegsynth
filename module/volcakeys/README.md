# Volca Keys Module

The purpose of this module is to write control values and notes as MIDI commands to the Korg Volca Keys.

Setting the MIDI channel: While holding down the MEMORY button, turn on the Volca. Specify the channel and press the REC button.

![VolcaKeys](./volcakeys.jpg)

## Requirements

The REDIS buffer should be running.
The Volca Keys should be connected over MIDI.

## Software Requirements

portmidi
Python 2.x
mido Python library
Redis Python library
