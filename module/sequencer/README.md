# Sequencer Module

This module implements a monophonic sequencer. It repeatedly plays a pre-configured sequence of notes to the Redis buffer. Using either the endorphines, outputcvgate or outputmidi module these notes can subsequently be sent to an external CV/Gate or MIDI device.

The sequencer supports up to 128 sequences of arbitrary length. You can use a MIDI channel (e.g. from the launchcontrol module) to directly select the sequence, or you can use a trigger to scroll to the next or previous sequence.

This sequencer requires an external clock: you can use the generateclock module or for example a combination of the heartrate module with the clockmultiplier/clockdivider module to trigger the steps of the sequence.
