# Contributing to EEGsynth development

There are many performances that can be built using the EEGsynth, not only interfacing EEG to an analog control voltage, but also interfacing other systems used in performances using e.g. MIDI, OSC, DMX, Artnet. That being said, there are also things that the EEGsynth cannot do, or is not so good at. Bellow follows a wish-list for which we hope that others can contribute.

## Precise timing of light effects

The modules that interface with lighting systems over Artnet and DMX work fine for slowly changing effects, but are not so good at sudden events. E.g. flashing upon a heartbeat or stroboscopic effects don't really work reliably. It would be nice to have better timing control of light effects.

## More affordable EEG hardware

Although we support and use different EEG systems (Gtec, OpenBCI, etc.), none of them is really affordable and easy to use. The OpenBCI system is not that expensive, but is very much a DIY system that comes as a bare PCB board without enclosure. It would be nice to have a low-cost and easy to use EEG system that comes with an enclosure including a standard AA battery holder and standard electrode connectors. 

