# Generate clock module

The goal of this module is to generate regular clock signals. The clock rate scales with a continuous control value. The output is sent as message to the Redis buffer and as clock ticks to MIDI. The Redis and MIDI messages are synchronous, but can be shifted relative to each other.

The MIDI clock ticks are always send 24 times per quarter note, or 96 times per whole note. The Redis messages are sent once per whole note, or more frequently if you increase the step value. Allowed step values are 1,2,3,4,6,8,12,24. You can shift the MIDI clock ticks relative to Redis messages using the adjust value (between -12 and 12).

The multiplier for the clock rate is exponentially mapped as 2^value and quantized to an integer division or multiplication. For example, the multiplier values -2,-1,0,1,2 are mapped to 1/4,1/2,1,2,4.

The clock rate is limited between 40 and 240 beats per minute.
