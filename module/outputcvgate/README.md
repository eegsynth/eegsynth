# Output CV/Gate Module

The goal of this module is to read control values from the Redis buffer and writes a serial output command to the Arduino-based USB to CV/Gate converter. See [this](https://github.com/eegsynth/eegsynth/tree/master/hardware/usb2cvgate_1channel) description for the 1-channel and [this](https://github.com/eegsynth/eegsynth/tree/master/hardware/usb2cvgate_4channel) desciption for the 4-channel hardware.

## Alternatives

An alternative to this module are the [Endorpines](http://www.endorphin.es/) Shuttle control, which is supported with its own EEGsynth module. Other alternatives that are not yet supported with EEGsynth are the Expert Sleepers [ES3](http://www.expert-sleepers.co.uk/es3.html), the Doepfer [A-190-1](http://www.doepfer.de/a190.htm), [A-190-2](http://www.doepfer.de/a1902.htm) and [MCV4](http://www.doepfer.de/mcv4.htm), and the Kenton [Modular-SOLO](http://www.kentonuk.com/products/items/m-cv/modsolo.shtml) and [Pro-SOLO](http://www.kentonuk.com/products/items/m-cv/prosolo.shtml).
