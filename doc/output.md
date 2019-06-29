# Output to software and devices

The purpose of the EEGsynth is to control external software and hardware with electrophysiological signals. Originally developed to control modular synthesizers, the EEGsynth supports most protocols for sound synthesis and control with output modules. These modules output events from Redis to their respective protocols.

- [MIDI](https://www.midi.org/), using the [outputmidi module](../module/outputmidi). Read more about how the EEGsynth
  works with MIDI [here](midi.md).
- [Open Sound Control](http://opensoundcontrol.org/introduction-osc) with the [outputosc module](../module/outputosc).
  This can also be used to control music software such as [Pure Data](https://puredata.info/)
  for which one can find [many applications](https://patchstorage.com/platform/pd-extended/) in music, art, games and science.
- [DMX512](https://en.wikipedia.org/wiki/DMX512) with the [outputdmx module](../module/outputdmx)
- [Art-Net](https://en.wikipedia.org/wiki/Art-Net) with the [outputartnet module](../module/outputartnet)
- Custom [CV/gate hardware](../hardware/usb2cvgate_4channel) using the [outputcvgate module](../module/outputcvgate) or commercial [CV/gate interfaces](doepfer.md) using the [outputmidi module](../module/outputmidi) and [endorphines module](../module/endorphines)
- When using a [Raspberry Pi](http://raspberrypi.org/), one can also control the general purpose input/output (GPIO) pins using the [outputgio module](../module/outputgpio)
- We have developed interfaces to other hardware/software, see the [module overview](module-overview.md)

## Accessing EEGsynth with external software

The output of modules to Redis can also be accessed directly (externally), e.g. for games using [PyGame](https://www.pygame.org/news).

## Other applications

- [TouchOSC](https://hexler.net/products/touchosc) is a closed source application for iOS or Android.
- [TouchOSC Bridge](https://hexler.net/docs/touchosc-getting-started-midi) is a closed source application for macOS and Windows.
- [MidiOSC](https://github.com/jstutters/MidiOSC) is an open source C++ application that uses the RtMidi interface.
- [OSCulator](http://www.osculator.net) is a closed source application for macOS.
- [AVMixer](https://neuromixer.com/products/avmixer-pro) is a closed source application for macOS. [Here](avmixer.md) is how we
  have integrated it in several performances.

## Calibration

Every output device or application need its own calibration. Read more about it [here](calibration.md).

_Continue reading: [Manual control](manual-control.md)_
