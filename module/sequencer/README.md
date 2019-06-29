# Sequencer Module

This module implements a monophonic sequencer. It repeatedly plays a pre-configured sequence of notes to the Redis buffer. Using either the endorphines, outputcvgate or outputmidi module these notes can subsequently be sent to an external CV/Gate or MIDI device.

The sequencer supports up to 128 sequences of arbitrary length. You can use a MIDI channel (e.g. from the launchcontrol module) to select the active sequence.

This sequencer requires an external clock to trigger the steps of the sequence: you can use the generateclock module, or for example a combination of the heartrate module with the clockmultiplier/clockdivider module.
