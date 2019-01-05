# Ini files

Every module directory contains an initialization file, which has the same name as the module and an *.ini* extention.
The initialisation file is a text file, formatted according to Python’s 
[ConfigParser class](https://docs.python.org/2/library/configparser.html). 
You can easily edit the files with any text editor.
The text is organized in fields defined between square brackets (e.g. ```[general]```), followed by
settings that ... with an equal sign (e.g. ```debug=1```). 

The ini file contains all the settings of a module. Some fields occur specific for a module, while 
many occur in almost all modules. We will discuss the latter below. Information about module specific 
configurations can be found in the _README.md_ in the module directory.

## ```[general]```

```delay``` sets the delay between each iteration of the module's internal loop, defined in seconds. 
A value of 0.05 means that the module will run through one iteration - e.g. calculate and output its 
results - 20 times per second. In our personal experience, this seems to be a reasonable trade-off between 
load and performance. 
 
```debug``` sets the degree of output send to the terminal for debugging purposes. A value of 0 will 
not output any debugging information, with values from 1 to 3 it will progressively add more, depending on the module.

## ```[fieldtrip]```

The EEGsynth uses the [FieldTrip buffer](buffer.md) to communicate data (e.g. several EEG channels) 
between modules. Note that the following settings have to be consistent with the ini file 
of the buffer module.

```hostname``` specifies the location of the FieldTrip buffer server. In the typical scenario when 
everything runs locally, use: ```hostname=localhost```

```port``` sets the port number of the FieldTrip server. For historical purposes, we typically set
it as: ```port=1972```

## ```[redis]```

The EEGsynth uses a [Redis database](http://Redis.io/) to communicate *control signals*, which are any 
discrete values that are set and read by the modules. Note that the following settings have to be 
consistent with the configuration of the Redis server (see [installation](installation.md)).
 
```hostname``` specifies the location of the FieldTrip buffer server. In the typical scenario when 
everything runs locally, use: ```hostname=localhost```
 
```port``` sets the port number of the FieldTrip server. Conventionally, we typically set
it as: ```port=6379```

## ```[output]```

Most modules output values (back to) the Redis database to be used by other modules. In the output field
you can specify the name under which they are written to the Redis database. Often this happens by 
prefixing or postfixing an input, as e.g. ```spectral.channel1.alpha``` by the spectral module:

```prefix=spectral```

## Manual control
Although the purpose of the EEGsynth (and BCIs in general) is to control devices using biological signals, some manual interaction might be desired, e.g. to adjust the dynamics of the output or to select the frequency range of the brainsignal during the recording. However, as with analogue synthsizers, we like the tactile real-time aspect of knobs and buttons, but would like to avoid using a computer keyboard. We therefor mainly use MIDI controllers, such as the [LaunchControl XL](https://global.novationmusic.com/launch/launch-control-xl#) displayed below. Identical to all other modules, the launchcontrol *module* records the launchcontrol input from sliders, knobs, and buttons into the Redis database to be used by other modules.

![](https://novationmusic.com/sites/novation/files/LCXL-HeaderImage-2560-1000.png)

*The Novation LaunchControl XL, often used in EEGsynth setups*

_Continue reading: [Patching](patching.md)_
