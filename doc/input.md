# Input of electrophyiological signals

We mostly use the low-cost and open hardware of the [OpenBCI](http://openbci.org/) project, using the command-line based [openbci2ft module](https://eegsynth/eegsynth/module/openbci2ft) or the OpenBCI GUI in combination with [Lab Streaming Layer](https://github.com/sccn/labstreaminglayer) and the [lsl2ft module](https://eegsynth/eegsynth/module/lsl2ft).

However, EEGsynth can also interface with other hardware such as the [Bitalino](https://bitalino.com) biosignal board and the [bitalino2ft module](https://eegsynth/eegsynth/module/bitalino2ft), the computer's audio input using [audio2ft module](https://eegsynth/eegsynth/module/audio2ft) or numerous state-of-the-art commercial EEG and MEG devices using FieldTrip's [device implementations](http://www.fieldtriptoolbox.org/development/realtime/implementation).

_Continue reading: [Output to software and devices](output.md)_
