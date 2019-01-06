# Controlling external software and hardware

The purpose of the EEGsynth is to control external software and hardware 
with electrophysiological signals. Originally developed to control modular 
synthesizers, the EEGsynth supports most protocols for sound synthesis and 
control with output modules. These modules output events from Redis to their respective protocols.

* [CV/gate](https://en.wikipedia.org/wiki/CV/gate) using the [outputCVgate module](../module/outputcvgate) 
* [MIDI](https://www.midi.org/), using the [outputMIDI module](../module/outputmidi). Read more about how the EEGsynth
works with MIDI [here](midi.md).
* [Open Sound Control](http://opensoundcontrol.org/introduction-osc) with the [outputOSC module](../module/outputosc). 
This can also be used to control music software such as [Pure Data](https://puredata.info/) 
for which one can find [many applications](https://patchstorage.com/platform/pd-extended/) in music, art, games and science.
* [DMX512](https://en.wikipedia.org/wiki/DMX512) with the [outputDMX module](../module/outputdmx512) 
* [Art-Net](https://en.wikipedia.org/wiki/Art-Net) with the [outputartnet module](../module/outputartnet)
* When using a [Raspberry Pi](), one can also control the general input/output pins ([gpio]()) using the [outputgio module](../module/outputgpio) 
* For several other consumer hardware interfaces we've developed mainly for our personal use, see the [module overview](module-overview.md)
 
## Accessing EEGsynth with external software 

Values that modules outputs to Redis can also be accessed directly (externally), e.g. for games using [PyGame](https://www.pygame.org/news). 

## Other applications

* [MidiOSC](https://github.com/jstutters/MidiOSC) is an open source C++ application that uses the RtMidi interface.
* [TouchOSC Bridge](http://hexler.net/docs/touchosc-getting-started-midi) is a closed source application for macOS or Windows.
* [OSCulator](http://www.osculator.net) is a closed source application for macOS.
* [AVMixer](https://neuromixer.com/products/avmixer-pro) is a closed source application for macOS. [Here](avmixer.md) is how we 
have integrated it in several performances.

## Calibration

Every output device or application need their own calibration. Read more about it [here](calibration.md).

_Continue reading: [Manual control](manual-control.md)_
