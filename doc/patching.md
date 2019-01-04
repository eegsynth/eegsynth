# Patching a module

In the EEGsynth, each module runs independently (in parallel), performing a specific function 
and communicating the result with each other. There is 
a great benefit in allowing modules to run independently, in their own time (anachronistically). 
In this way, some modules can run fast (e.g. pulling new data from an external device, and putting
it in the data buffer), while others can run at a 'slower' pace, e.g. calculating power over second-long windows. 
 
A basic patch might have the following run (in parallel):
 * **[Redis server](redis.md)** to communicate _control signals_ between modules
 * The **[buffer module](buffer.md)** to communicate _data_ between modules
 * The **[OpenBCI module](../module/openbci2ft)** reading new ECG data from an OpenBCI board and placing it in the _data_ buffer
 * The **[heartrate module](../module/heartrate)** reading new ECG data from the data buffer and sending the heartrate as a _control signal_ 
 to Redis
 * The **[generateclock module](../module/generateclock)** sending regular triggers through MIDI to a sequencer, 
 with the speed dependent on the heartrate read from Redis 

As you can see here, there are two ways in which the modules communicate, depending on whether **data** or
**control signals** are communicated. This is a similar distinction as made in e.g. Pure Data (software) or modular 
synthesizers (hardware). 

## Control signal communication

In the EEGsynth patching (communication) between modules is implemented through 
a [Redis database](redis.md). Interactions with Redis - which fields to read and where to write - are specified 
in each module's [ini file](inifile.md). For example, the [spectral module](../module/spectral), this
might read from Redis the frequency bands in Hz, and write its output (power in those frequency bands)
back into Redis. Or, to take the above example, the [generateclock module](../module/generateclock)
will read from Redis the heartrate in seconds. It might output triggers directly to [MIDI](midi.md) 
as well as send pub/sub events back to Redis.  
  

## Data communication



## Editing and organizing your patches

Each module directory contains an ini file in their respective directory, with a filename identical 
to the module. E.g. [module/spectral](https://github.com/eegsynth/eegsynth/tree/master/module/spectral)
contains [spectral.py](https://github.com/eegsynth/eegsynth/tree/master/module/spectral/spectral.py) 
and [spectral.ini](https://github.com/eegsynth/eegsynth/tree/master/module/spectral/spectral.ini). 

This ini file shows the required fields and some default values. However, you should save your 
edited ini files in a separate 'patch directory'. In this patch directory you store all the .ini files 
belonging to one patch. This helps organizing your patches as well as your local git repository, 
which will then not create conflicts with the remote (default) .ini files.
You can find several examples of patch directories in the [patches directory](https://github.com/eegsynth/eegsynth/patches).
These also function as documentation of past performances. 
