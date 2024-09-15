# InputLSL

This module receives event messages from LabStreamingLayer (LSL) and sends them to Redis.

Note that this module is explicitly designed for irregular string-valued LSL messages, not for data. If you want to process regularly sampled data such as EEG, you should use the lsl2ft module.

A limitation of the LSL marker format is that it only contain a single string value. Under the `[lsl]` section you can specify by the format whether you want the LSL marker string to be interpreted as a string that becomes part of the Redis message, or as a numeric value.
