# FieldTrip buffer

The EEGsynth uses the [FieldTrip buffer](http://www.fieldtriptoolbox.org/development/realtime/buffer) to exchange electrophysiological data between modules. It is the place where raw time-course (or processed) data is streamed.

Modules such as [unicorn2ft](../src/module/unicorn2ft), [openbci2ft](openbci.md), and [bitalino2ft](../src/module/bitalino2ft) take care of data acquisition, interfacing with acquisition devices and updating the FieldTrip buffer with incoming data.

Some modules, such as the [spectral](../src/module/spectral) module, take data from the FieldTrip buffer as input, then outputs values to the [Redis buffer](redis.md).

Finally, some modules, such as the [preprocessing](../src/module/preprocessing) module, filters and preprocessing raw data from one buffer, and writes results to another raw data buffer.

Note that the FieldTrip buffer allows reading of data by multiple modules at the same time. For more information on the FieldTrip buffer, check the [FieldTrip documentation](https://www.fieldtriptoolbox.org/development/realtime/buffer). For some examples of accessing the [FieldTrip buffer](https://www.fieldtriptoolbox.org/development/realtime/buffer) see the [documentation of the module scripts](scripts.md).
