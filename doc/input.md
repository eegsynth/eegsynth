# Input of electrophyiological signals

For EEG we mostly use the [Unicorn](https://www.unicorn-bi.com) EEG system in conbination with the [unicorn2ft](../src/module/unicorn2ft) module. Although the Unicorn comes with its own Windows-only software for signal visualization and for streaming to LSL, the unicorn2ft module does not depend on the Unicorn software, is Python-only, and also runs on macOS and Linux.

For EMG we commonly use the low-cost [OpenBCI](http://openbci.org/) Ganglion amplifier, using the OpenBCI GUI in combination with [Lab Streaming Layer](https://github.com/sccn/labstreaminglayer) and the [lsl2ft module](../src/module/lsl2ft).

The EEGsynth can also interface with other hardware such as the [Bitalino](https://bitalino.com) biosignal board using the [bitalino2ft module](../src/module/bitalino2ft), the computer's audio input using [audio2ft module](../src/module/audio2ft) or numerous state-of-the-art commercial EEG and MEG devices using FieldTrip's [device-specific implementations](http://www.fieldtriptoolbox.org/development/realtime/implementation).

_Continue reading: [Output to software and devices](output.md)_
