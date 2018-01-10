# Endorphines Module

The purpose of this module is to send control values from REDIS to the Endorphin.es Shuttle Control. The Shuttle Control is a MIDI to CV/Gate converter with 16 channels that can be controlled from -5 to +5 Volt.

![Endorphin.es Shuttle Control](./shuttle-control.jpg)

## Alternatives

Alternatives to this module are the DIY [1-channel](https://github.com/eegsynth/eegsynth/tree/master/hardware/usb2cvgate_1channel) and [4-channel](https://github.com/eegsynth/eegsynth/tree/master/hardware/usb2cvgate_4channel) USB-to-CV/gate converters that we made for EEGsynth and that are supported by the *outputcvgate* module. Other alternatives that are not yet supported with EEGsynth are the Expert Sleepers [ES3](http://www.expert-sleepers.co.uk/es3.html), the Doepfer [A-190-1](http://www.doepfer.de/a190.htm), [A-190-2](http://www.doepfer.de/a1902.htm) and [MCV4](http://www.doepfer.de/mcv4.htm), and the Kenton [Modular-SOLO](http://www.kentonuk.com/products/items/m-cv/modsolo.shtml) and [Pro-SOLO](http://www.kentonuk.com/products/items/m-cv/prosolo.shtml). 

## Requirements

The REDIS buffer should be running.
The Shuttle Control module should be connected on the USB port.
The channels of the Shuttle Control should be configured as "Pitchwheel" and should use MIDI channel 1-16.

## Software Requirements

Python 2.x
portmidi
mido
redis
