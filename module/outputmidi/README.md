# Output MIDI Module

The purpose of this module is to send triggers and control values from Redis to an external MIDI device. The mapping between triggers and control channels can be fully configured in the ini file.

In the EEGsynth we are using two different mechanisms for communication. Continuous control channels are represented in Redis using *set/get*, which allow relatively slowly changing values to be represented persistently. Triggers are represented in Redis using *publish/subscribe*, which allows precise timing of events to be synchronized.


## Triggers

Under the `[trigger]` section you specify the mapping between MIDI messages and Redis messages. The MIDI message are triggered immediately by Redis messages.

You can specify MIDI *note_on* messages using `noteXXX` where XXX is the MIDI note number. For example you can specify `note060` to play the [C4](https://newt.phys.unsw.edu.au/jw/notes.html)).

You can specify MIDI *control_change* and *polytoch* messages using `controlXXX` and `polytouchXXX`, where XXX is the MIDI control channel.

You can also specify MIDI *aftertouch*, *pitchwheel*, *start*, *continue*, *stop* and *reset* messages. These are without an additional number, since they do not apply to a specific note or control.


## Continuous control channels

Under the `[control]` section you specify the mapping between MIDI messages and Redis channels. Upon starting this module, the initial values will be sent as MIDI messages. Subsequently, the value of the Redis channels are sampled regularly (given the `delay` parameter) and sent as MIDI messages if the value changes.

The specification of the mapping between MIDI messages and Redis is the same as for triggers.


## Using start, stop, continue and reset for a sequencer

You can use the launchcontrol module to map buttons to the start and to the stop messages. Since the start and stop message do not have a value, you have to use different buttons for start and stop.

If you configure them as triggers in this module, you should configure them as `slap` buttons in the launchcontrol module, otherwise the MIDI message gets sent twice (once upon press, once upon release).

If you configure them as control channels in this module, you should configure them either as `push` or as `slap` buttons in the launchcontrol module and not as latching `toggle` buttons.
