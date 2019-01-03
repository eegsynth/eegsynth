# Design of the EEGsynth

The design of the EEGsynth is modular, directly inspired by 
[modular synthesizers](https://en.wikipedia.org/wiki/Modular_synthesizer) (see picture below). 
Every module does a specific task. Each module consists of a python script, and is contained in its own directory. 
For instance, in [eegsynth\modules\launchcontrol](https://github.com/eegsynth/eegsynth/modules/launchcontrol) we find:
 * [launchcontrol.py](https://github.com/eegsynth/eegsynth/modules/launchcontrol/launchcontrol.py) The [Python](https://www.python.org/) script
 * [launchcontrol.ini](https://github.com/eegsynth/eegsynth/modules/launchcontrol/launchcontrol.ini) The initialization file setting the parameters and the way it's connected 
 * [README.MD](https://github.com/eegsynth/eegsynth/modules/launchcontrol/README.MD) The explanation of the module in [markdown]() format 

Similarly as in modular synthesizers, the EEGsynth functions when several modules are interconnected, sending 
and receiving information from each other. How each module is connected with the others is configured in 
their initiation file. 

Each module is executed in parallel, independently, performing a particular function and communicating with each other. There is 
a great benefit in allowing modules to run independently, in their own time (anachronistically). In this way, 
some modules can run fast (e.g. pulling new data from an external device), while others can have a slower pace
(e.g. calculating power over second-long windows). 
 
A basic patch might have the following run (in parallel). 
Don't worry, we will explain all of the parts shortly:
 * **Redis server** to communicate _control signals_ between modules
 * The **buffer module** to communicate _data_ between modules
 * The **OpenBCI module** reading new ECG data from an OpenBCI board and placing it in the _data_ buffer
 * The **heartrate module** reading new ECG data from the data buffer and sending the heartrate as a _control signal_ 
 to Redis
 * The **generateclock module** sending regular triggers through MIDI to a sequencer, with the speed dependent on the 
 heartrate read from Redis 

As you can see, there are two ways in which the modules communicate, depending o whether it is **data** or a
**control signal** that is communicated. This is a similar distinction as made in e.g. Pure Data (software) or modular 
synthesizers (hardware). 

In the EEGsynth patching (communication) between modules is implemented through the use of the open-source 
[Redis database](http://Redis.io/) which stores 
[attribute-value pairs](https://en.wikipedia.org/wiki/Attribute%E2%80%93value_pair), i.e. a name associated
with a value, such as ('Name', 'John') or ('Height', 1.82). A module can put anything it wants into the 
database, such as ('Heartrate', 92). Another module can ask the database to return the value belonging to 
('Heartrate'). This allows one to create anything from basic 'linear' patches, to complex, many-to-many connections.

Interactions with Redis are specified separately for each module in their own* .ini* file. More information about 
the ini files is explained [here](inifile.md).  

