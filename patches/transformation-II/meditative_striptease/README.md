# TRANSFORMATION-II Meditative Striptease

This directory contains the EEGsynth patch for "Meditative Striptease" performed live for TRANSFORMATION-II on 3 May 2020 20:00-21:00 by Carima Neusser and Per Hüttner on [∏Node radio](https://p-node.org/.

# Technical details

The patch starts with the signals from a 4-channel [OpenBCI Gangion amplifier](http://www.eegsynth.org/?p=2034). One bipolar EEG channel is used, connected to Per, and one bipolar EMG channel, connected to Carima.

The the brain (EEG) and muscle (EMG) signals are processed separately, using settings optimized for the respective signal characteristics. The signals are converted into continuous control channels, amplitude normalized, slew-limited and dynamically compressed.

Subsequently the control channels are converted in MIDI signals and send (over WiFi) to another computer running Ableton Live.
