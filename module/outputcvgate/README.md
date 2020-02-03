# Output CV/Gate module

This module reads control values from the Redis buffer and writes a serial output command to the Arduino-based USB to CV/Gate converter. See [this](https://github.com/eegsynth/eegsynth/tree/master/hardware/usb2cvgate_1channel) description for the 1-channel and [this](https://github.com/eegsynth/eegsynth/tree/master/hardware/usb2cvgate_4channel) description for the 4-channel hardware.

The module supports two modes of operation. If you specify the Redis channel in the `[input]`, its value will be regularly polled and sent to the hardware interface. If you specify the channel in `[trigger]`, it uses the publish-subscribe mechanism and sends the updated values to the hardware interface immediately. The latter is preferred for instantaneous control.

## Alternatives

An alternative to this module is the [Endorpines](http://www.endorphin.es/) Shuttle control, which is supported with its own EEGsynth `endorphines` module.

Other alternatives that can be used in combination with the EEGsynth `outputmidi` module are the Doepfer [A-190-1](http://www.doepfer.de/a190.htm), [A-190-2](http://www.doepfer.de/a1902.htm) and [MCV4](http://www.doepfer.de/mcv4.htm), the Expert Sleepers [ES3](http://www.expert-sleepers.co.uk/es3.html), and the Kenton [Modular-SOLO](http://www.kentonuk.com/products/items/m-cv/modsolo.shtml) and [Pro-SOLO](http://www.kentonuk.com/products/items/m-cv/prosolo.shtml).
