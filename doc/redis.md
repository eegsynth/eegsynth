# Redis

## TL;DR explanation

The EEGsynth implements patching modules by means of the 
open-source [Redis database](http://Redis.io/). In the code, modules _put_ [attribute-value pair](https://en.wikipedia.org/wiki/Attribute%E2%80%93value_pair) 
into the database, e.g. ```put('Heartrate', 92)```, or request the value 
of an attribute, e.g. ```get('Heartrate')```. In addition, modules publish/subscribe 
and can respond near instantly to singular events or to changes in continuous values. 
The user of the EEGsynth specifies the attribute names for input and output in each module's 
[initialization file](inifile.md), and often adds prefixes or postfixes to the input attributes. 
Because the Redis database is network-transparent, it can easily be accessed via e.g. other 
programs, e.g. with Python (see documentation on [output and control](output.md))

## Extended explanation

### Introduction

Processes in the body and brain - and their analysis - can be considers to have two categorically different ways of relating to time: 
they are either continuous, or they consist of momentary events. Power within a particular frequency 
range is an example of the former, while the occurrence of a heart-beat 
would be an example of an event. Both are implemented using a database ([Redis](http://Redis.io/)), 
with put/get for continuous signals, and pub/sub (publish/subscribe) to deal with events. 
To understand how this works in practical contexts, such as when controlling a modular synthesizer, 
we need to translate terms, and get from _events_ to the modular language of _triggers_ and _gates_.

### Electrophysiological Events

We use the term ‘event’ to describe the identification of a meaningful moment in time. 
In EEG analysis this refers to what are called event-related potentials (ERPs): 
electrical potentials that the brain generates when something specific happens, for instance 
in direct response to a particular kind of picture, or sound, or the moment you decide to press 
a button. Those brain responses are often impossibly hard to decode based on a single occurrence, 
and are typically repeated hundreds of times to extract them from the ‘noise’ of instrumentation and 
background brain activity. Approaches using machine-learning algorithms might be a able to catch some ERPs 
sometimes, a concept that was cleverly explored in the sonic art-neuroscience performance 
[Ringing Minds (2014)](http://www.antillipsi.net/art-1/bioart), by Tim Mullen, David Roosenboom, and others. 
They did not use repetitions over time, but rather _multiple brains at the same time_ to extract significant 
events from the brains of the participants. Another solution might be to use brains that produce 
very large brain events spontaneously, such as in epilepsy. For most intents and purposes,
however, EEG just does not provide much to work with when it comes to events. Instead we can look at other 
electrophysiological signals, such as electrocardiography (ECG). With ECG we can clearly identify ‘events’, 
namely heart-beats, e.g. detected by the R-peak of the QRS complex. We know the time between 
heart-beats, the inter-beat-interval (or it’s inverse: the heart-rate), has physiological meaning 
(heart-rate variability is a reliable indicator of physiological health), displays variation over time, 
and can be brought to some degree under conscious control via biofeedback, altogether making it a 
very interesting signal to explore in performances and music.

### Gates and triggers

In the world of modular synthesizers we deal with _triggers_ and _gates_. Whether it be the press 
of a key on a keyboard, the output of a clock, the passing of an audio-threshold, when something has to start a trigger 
is used. A trigger is a short electrical pulse (typically 5-10v for about 3ms) that can start an envelope, 
proceed to the next step in a sequencer, provide a tick for another clock, etc. 
What is important in terms of implementation in the EEGsynth, is to realize that a trigger has no duration. 
So as a way to code an event, it only codes for the beginning (or end) of an event. 
Gates, however, do have duration. They are used exactly for that purpose: to code for the duration of events 
by being open (5-10v) during the event, and closed (0v) otherwise. A gate is can be used e.g. to code the output of
logical operators (TRUE or FALSE), whether or not an LFO is cycling or not, whether a sample-loop is playing, etc. 
Because of the way triggers are implemented in modular synthesis (upgoing voltage from 0 to 5v), a gates can often 
be used as a trigger. In the EEGsynth, however, the implementation is very different, as one would be coded as a 
continuous value that is turned either on or off via a put/get operation, while triggers are singular events
that modules _publish_ and to which other modules _subscribe_. 

![Trigger](figures/trigger.png)
_A trigger signal_

![Gate](figures/gate.png)
_A gate signal_

### Bringing two worlds together

In the EEGsynth modules communicate either control signals, or data. Data is communicated via the [FieldTrip buffer](buffer.md),
while control signals are distributed between modules via the [Redis database](http://Redis.io/).
Control signals can be either continuous, analogous to Control Voltages (and gates) in modular synthesis, 
or momentary, analogous to triggers in modular synthesis. 

In the case of continuous control signals, the database contains key-value pairs, with the name of 
the control signal (e.g. ‘alpha’) and a value [typically calibrated](calibration.md) between 0 and 1. 
These values are read and updated by the modules in real-time. At any point in time, you are able to read the 
state of all the (CV) control values by reading the content of that database. It would be the same 
as taking a multimeter and measuring the currents on all the wires on a modular synthesizer 
at the same time! The reason that this is such a good way of implementing control values, is 
that it’s asynchronous: modules don’t have to read and update the values continuously, only 
whenever they need the information, or whenever they have a value to update. This is important
to understand. It’s the core of the EEGsynth, and why it is able to run many modules at the 
same time, at different rates (some are complex and slow, some are simple and fast, some care,
some don’t), without having to wait for each other: they always get the latest update, 
whenever they want, and can continue even when those values are not updated yet.
 
When dealing with triggers, the whole point of triggers is to be precise in 
time – to indicate _when_ something HAS happened (or has to happen). The solution to this is to use another 
way of communicating; Rather than having a general 
repository to _put_ or _get_ information, we can use a _pub/sub_ way of messaging between modules. 
‘Pub’ stands for _publishing_, while ‘sub’ stands for _subscribe_. So rather than modules updating 
a value in a database where it will stay for whenever it is needed, they can give a shout-out, e.g.  
“Heartbeat trigger detected, read all about it!”, to whichever module subscribed to it. 
This makes the communication near instant, i.e. _synchronous_. A module that needs to respond 
to a heartbeat would therefor not have to keep looking at the database as often as possible, 
increasing CPU load and memory access, but just 
subscribe to the module publishing those events, then waiting until they get a message to which 
they can respond instantly. That's how we implement triggers.

## Final thoughts

After correct [installation](installation.md), you should have Redis running in the background. 
You can open a Redis interface by typing: ```redis-cli```. You can then ```put('myname','blabla')``` 
and ```get('myname')```, to return the value ('blabla').
Another great trick, is to monitor changes in the content of Redis while the EEGsynth is running, by opening a 
new terminal and running ```redis-cli monitor```.


