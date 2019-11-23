# OutputLSL

This module sends triggers and control value changes from Redis to LabStreamingLayer (LSL).

In the EEGsynth we are using two different mechanisms for communication. Continuous control channels are represented in Redis using *set/get*, which allow relatively slowly changing values to be represented persistently. Triggers are represented in Redis using *publish/subscribe*, which allows precise timing of events to be synchronized.

A limitation of the LSL marker format is that it only contain a single string value. Under the `[lsl]` section you can specify by the format whether you want the LSL marker string to represent the Redis name, or the Redis value.

## Triggers

Under the `[trigger]` section you specify the mapping between LSL string markers and Redis messages. The LSL markers are triggered immediately by Redis messages.

## Continuous control channels

Under the `[control]` section you specify the mapping between LSL markers and Redis channels. Upon starting this module, the initial values will be sent as LSL markers. Subsequently, the value of the Redis channels are sampled regularly (given the `delay` parameter) and sent as LSL markers if the value changes.
