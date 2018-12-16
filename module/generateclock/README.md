# Generate clock module

The goal of this module is to generate regular clock signals. The rate of these clock signals is determined by a continuous control value. The output is sent as message to the Redis buffer and as clock ticks to MIDI. The Redis and MIDI messages are synchronous.

The MIDI clock ticks are always send 24 times per quarter note, or 96 times per whole note. The MIDI clock signals will start ticking whenever the *play* parameter switches to true. This can be hardcoded as "1" in the ini file, but can also be mapped to a toggle button that is represented as control channel in Redis. The MIDI start signal will be sent whenever the *start* parameter switches to true. This can be hardcoded as "1" in the ini file, but can also be mapped to a toggle button that is represented as control channel in Redis. The MIDI stop signal will be sent whenever the *start* parameter switches to false. If you do not want the MIDI start and stop signal to be sent (e.g. when your hardware device has a button), you should leave the *start* parameter empty.

The rate of the Redis messages is controlled by the *ppqn* (pulse per quarter note) parameter. Since Redis messages are aligned with the MIDI clock ticks, only integer divisors are possible. You can specify values of 1,2,3,4,6,8,12,24, where 1 means one pulse per quarter note. You can shift the Redis messages relative to the MIDI clock ticks by a quarter note using the *shift* parameter (between -12 and 12).

The clock rate is limited between 40 and 240 beats per minute.
