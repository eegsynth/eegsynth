# EEGsynth scripts

As explained [here](design.md), the EEGsynth is designed as a collection of modules, where each 
module addresses a singular function. Modules are [patched](patching.md) together to
provide a flexible system to achieve your particular goal.

## Starting the scripts

The core of each modules consists of a [Python](https://python.org) script. These scripts are 
executed in their own terminal window (or tab) as a Python script, 
with the ```-i``` option followed by the path to their [ini file](inifile.md). 

For example:

```python launchcontrol.py -i ../../patches/launchcontrol.ini``` 

If the script is run without the ```-i``` option, it will default to the ini file in the
current path that has the same name as the module. As explained [here](patching.md), we strongly
advice you to place your edited [ini files](inifile.md) in a separate patch directory to keep
your patches organized and free from conflicts with the EEGsynth repository.

## Design of the scripts

To use the modules you do not need to be able to understand [Python](https://python.org) or be
able to program. However, for those who do want to [contribute](contribute.md), what follows is
an explanation of a 'skeleton' of code, that can be used to design you own module or extend the
functionality of an existing one (although as explained [here](contribute.md) we do adhere to
a modular design in which each module addresses a specific and limited function). When going
through the code of a script like that, you will notice that most of the code is, in fact, the same.

### Description and license

Each script is prefaced with a commented text explaining it's functionality, as well as GNU license.
Note that you are obliged to conform to the GNU General Public License (also in derived works): 

```
#!/usr/bin/env python

# Generatecontrol creates user-defined signals and writes these to Redis
#
# This software is part of the EEGsynth project, see https://github.com/eegsynth/eegsynth
#
# Copyright (C) 2017 EEGsynth project
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
```
(From [generatecontrol.py](../module/generatecontrol/generatecontrol.py))

### Importing libraries

The EEGsynth uses standard Python libraries as well as it's own, located in the /bin directory:

```
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import argparse
import numpy as np
import os
import redis
import sys
import time
from scipy import signal

if hasattr(sys, 'frozen'):
    basis = sys.executable
elif sys.argv[0]!='':
    basis = sys.argv[0]
else:
    basis = './'
installed_folder = os.path.split(basis)[0]

# eegsynth/lib contains shared modules
sys.path.insert(0, os.path.join(installed_folder,'../../lib'))
import EEGsynth
```
(From [generatecontrol.py](../module/generatecontrol/generatecontrol.py))

### The patch object

What follows is a couple of lines of code that read and combine settings from both the ini file
and Redis in a patch object. It is important to understand their interaction, as it account of a lot of
the EEGsynth's flexibility and real-time element:

* Values can be set by both the ini file and by Redis. None take priority - the last edit remains. 
* Any (running) module can set values in Redis, so multiple modules can read and write to Redis, allowing many-to-many interactions.
* Rather than values, the ini file can specify the name (a string) of anosther Redis key/attribute. 
In this way, one can have a values set by the result of an EEG analysis (e.g.: _spectral.channel1.alpha_)
or the knob of a MIDI controller (e.g.: _launchcontrol.control077_). 
* When a value is empty, the _patch object_ returns the default value set in the code. 

We try to permit _all_ dynamic values to be set dynamically like this, which is very conveniently
done using the _patch object_:

```
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inifile", default=os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'), help="optional name of the configuration file")
args = parser.parse_args()

config = ConfigParser.ConfigParser()
config.read(args.inifile)

try:
    r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
    response = r.client_list()
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

# combine the patching from the configuration file and Redis
patch = EEGsynth.patch(config, r)
del config


# this determines how much debugging information gets printed
debug = patch.getint('general','debug')

# the scale and offset are used to map Redis values to signal parameters
scale_frequency   = patch.getfloat('scale', 'frequency', default=1)
scale_amplitude   = patch.getfloat('scale', 'amplitude', default=1)
scale_offset      = patch.getfloat('scale', 'offset', default=1)
scale_noise       = patch.getfloat('scale', 'noise', default=1)
scale_dutycycle   = patch.getfloat('scale', 'dutycycle', default=1)
offset_frequency  = patch.getfloat('offset', 'frequency', default=0)
offset_amplitude  = patch.getfloat('offset', 'amplitude', default=0)
offset_offset     = patch.getfloat('offset', 'offset', default=0)
offset_noise      = patch.getfloat('offset', 'noise', default=0)
offset_dutycycle  = patch.getfloat('offset', 'dutycycle', default=0)
stepsize          = patch.getfloat('generate', 'stepsize') # in seconds

```
(From [generatecontrol.py](../module/generatecontrol/generatecontrol.py))

### Connecting to MIDI devices 

More about MIDI and the EEGsynth is explained [here](midi.md). 
MIDI devices can be accessed in de code using the EEGsynth library:

```
midiport = EEGsynth.midiwrapper(config)
midiport.open_output()
```
(From [generateclock.py](../module/generateclock/generateclock.py))

Sending MIDI messages can be send using [Python/MIDO](https://mido.readthedocs.org):

```
midiport.send(mido.Message('stop'))
```

To read MIDI input, please take as an example the [Launchcontrol module](../module/launchcontrol)

### Connecting to the FieldTrip buffer

Electrophysiological data is communicated to (and between) modules using the [FieldTrip buffer](buffer.md).
To connect to the FieldTrip buffer:

```
try:
    ftc_host = patch.getstring('fieldtrip','hostname')
    ftc_port = patch.getint('fieldtrip','port')

    if debug>0:
        print 'Trying to connect to buffer on %s:%i ...' % (ftc_host, ftc_port)

    ftc = FieldTrip.Client()
    ftc.connect(ftc_host, ftc_port)

    if debug>0:
        print "Connected to FieldTrip buffer"

except:
    print "Error: cannot connect to FieldTrip buffer"
    exit()
```

To wait until there is _any_ data we can wait until the data header is available: 

```
hdr_input = None
start = time.time()

while hdr_input is None:

    if debug>0:
        print "Waiting for data to arrive..."

    if (time.time()-start)>timeout:
        print "Error: timeout while waiting for data"
        raise SystemExit

    hdr_input = ftc.getHeader()
    time.sleep(0.2)
```

We can also use the _nSamples_ field in the header to wait for a specified number of samples:

``` 
hdr_input = ftc.getHeader()

if (hdr_input.nSamples-1)<endsample:
    print "Error: buffer reset detected"
    raise SystemExit
    
endsample = hdr_input.nSamples - 1

if endsample<window:
    # not enough data, try again in the next iteration
    continue
```

...and then read the data from the buffer: 

```
begsample = endsample-window+1
D = ftc.getData([begsample, endsample])
```

(From [spectral.py](../module/spectral/spectral.py))     
            
### Printing feedback to terminal

Sometimes it is useful to print information to the terminal. For debugging/prototyping purposes you might want 
to print more. We use the ```debug``` value from the [ini file](inifile.md) to specify the degree of verbosity,
so that in the code one might use:

```
if debug > 1:
    print "update", update
```
(From [generatecontrol.py](../module/generatecontrol/generatecontrol.py))

### Main loop

Within each module, we will have a main loop run through iterations until stopped: 
 
```
while True:
```

### Controlling speed of main loop

In most cases it is not necessary nor desirable to have every iteration directly follow the previous.
This might overburden (network) communication with the Redis server. It is generally just good policy to
control the speed of the processes. For this purpose a simple trick can be used, which keeps the
time of each iteration consistent with the ```delay``` parameter under the ```[general]``` field in the
[ini file](inifile.md):

```
while True:

    # determine the start of the actual processing
    start = time.time()

    <MAIN CODE>  
  
    elapsed = time.time()-start
    naptime = stepsize - elapsed

    if naptime>0:
        # this approximates the desired update speed
        time.sleep(naptime)
```
(From [generatecontrol.py](../module/generatecontrol/generatecontrol.py))

### Writing to Redis
 
In many cases, a module will output its results by changing some value(s) in Redis. 
Other modules can then read those values and use them to influence [output devices](output.md).
Setting a value in Redis using the _patch obect_ is as simple as:

```
patch.setvalue(key, value)
```

For example (from [generatesignal.py](../module/generatesignal/generatesignal.py)):

```
key = patch.getstring('output', 'prefix') + '.sin'
val = np.sin(phase) * amplitude + offset + np.random.randn(1) * noise
patch.setvalue(key, val[0])
```

### ADVANCED: Using (Multi)threading

The above way of iterating through the main code assumes two things: time is not of the essence,
and all the code can be executed sequentially. This is by far the easiest way to think and code.
However, sometimes it is necessary to have several processes running at the same time, especially
when time is of the essence, and the code should respond to an event as soon as it happens,
without waiting for other code to finish. In such cases it one should probably first try to 
see whether the intended scenario cannot be accomplished with two separate modules. If not, one 
might want to use threads.

Threads are started before the main loop, which then often only has to be there to allow those threads
to remain active and permit keyboard interrupts (CTRL+C) to be able to stop the code: 

```
class ClockThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running = True
        self.rate = 60              # the rate is in bpm, i.e. quarter notes per minute
    def setRate(self, rate):
        if rate != self.rate:
            with lock:
                self.rate = rate
    def stop(self):
        self.running = False
    def run(self):
        slip = 0
        while self.running:
            if debug>1:
                print 'clock beat'
            start  = time.time()
            delay  = 60/self.rate   # the rate is in bpm
            delay -= slip           # correct for the slip from the previous iteration
            jiffy  = delay/24
            for tick in range(24):
                clock[tick].set()
                clock[tick].clear()
                if jiffy>0:
                    time.sleep(jiffy)
            # the actual time used in this loop will be slightly different than desired
            # this will be corrected on the next iteration
            slip = time.time() - start - delay
            
```

Which is started by for the main loop by:

```
# create and start the thread that manages the clock
clockthread = ClockThread()
clockthread.start()
```

Followed by the main loop, and a neat closing of thread when it's interrupted:

```
while True:

    <MAIN LOOP>

except (KeyboardInterrupt, RuntimeError) as e:
    print "Closing threads"
    clockthread.stop()
    clockthread.join()
    sys.exit()
```

(From [generateclock.py](../module/generateclock/generateclock.py))

### ADVANCED: Using publish/subscribe

For examples on pubsub, take a look at the [keyboard module](../module/keyboard) and [launchcontrol module](../module/launchcontrol).

_Continue reading: [ini files](inifile.md)_

