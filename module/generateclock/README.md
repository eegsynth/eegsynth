# Generate clock module

The goal of this module is to generate regular clock signals. The rate of these clock signals is determined by a continuous control value. The output is sent as message to the Redis buffer and as clock ticks to MIDI. The Redis and MIDI messages are synchronous.

The MIDI clock ticks are always send 24 times per quarter note, or 96 times per whole note. Please note that this module will *not* send a MIDI start message, so you still have to start your sequencer by hand.

The rate of the Redis messages is controlled by the *ppqn* (pulse per quarter note) parameter. The Redis messages are aligned with the MIDI clock ticks, so values of 1,2,3,4,6,8,12,24 are allowed. You can shift the Redis messages relative to the MIDI clock ticks by a quarter note using the *shift* parameter (between -12 and 12).

The clock rate is limited between 40 and 240 beats per minute.
