# Output MIDI Module

The purpose of this module is to send triggers and control values from Redis to an external MIDI device. The mapping between triggers and control channels can be fully configured in the ini file.

In the EEGsynth we are using two different mechanisms. On the one hand we have continuous control channels using Redis *set/get*, which allow relatively slowly changing values to be represented persistently. On the other hand, we use Redis *publish/subscribe* to trigger precisely synchronized updates.

## Triggers

Under the `[trigger]` section you specify the mapping between MIDI messages and Redis keys. The MIDI messages as send as soon as the value of the Redis key changes.

You can specify MIDI *note_on* messages using `noteXXX` where XXX is the MIDI note number. For example you can specify `note060` to play the [C4](https://newt.phys.unsw.edu.au/jw/notes.html)).

You can specify MIDI *control_change* messages using `controlXXX` where XXX is the MIDI control channel.

## Continuous control channels

Under the `[control]` section you specify Redis channels that continuously should be sent as MIDI messages, regardless of whether they change. The rate at which the values are read from Redis and sent to MIDI is determined by the general `delay` parameter.

The specification of the mapping between Redis and MIDI is the same as for triggers. If you would specify `note060` and connect it to a MIDI piano, you would repeatedly hear the C4 being played, at the rate of the `delay` parameter.

Besides control channels, it is useful to have *start* and *stop* messages sent repeatedly. You could for example set up a patch to start a sequencer if the EEG alpha is above a certain threshold, and to stop it if the EEG alpha is too low.
