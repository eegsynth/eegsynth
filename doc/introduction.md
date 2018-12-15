# The EEGsynth

## Table of contents
* [Introduction](#user-content-introduction)
  * [Background](#user-content-background)
  * [Modular design and patching](#user-content-modular-design-and-patching)
  * [Data acquisition and communication](#user-content-data-acquisition-and-communication)
  * [Controlling external software and hardware](#user-content-controlling-external-software-and-hardware)
  * [Manual control](#user-content-manual-control)
  * [Summary](#user-content-summary)

# Introduction

What follows is a short introduction on the design and use of the EEGsynth, followed by tutorials to get you started creating your own BCI system.

## Background
The EEGsynth is a [Python](https://www.python.org/) codebase released under the [GNU general public license]( https://en.wikipedia.org/wiki/GNU_General_Public_License) that provides a real-time interface between (open-hardware) devices for electrophysiological recordings (e.g. EEG, EMG and ECG) and analogue and digital devices (e.g. MIDI, games and analogue synthesizers). This allows one to use electrical brain/body activity to flexibly control devices in real-time, for what are called (re)active and passive brain-computer-interfaces (BCIs), biofeedback and neurofeedback. The EEGsynth does *not* allow diagnostics, and neither does it provide a GUI for offline analysis. Rather, the EEGsynth is intended as a collaborative interdisciplinary [open-source](https://opensource.com/open-source-way) and [open-hardware](https://opensource.com/resources/what-open-hardware) project that brings together programmers, musicians, artists, neuroscientists and developers for scientific and artistic exploration.

* The EEGsynth is intended to be run from the command line, using [Python](https://www.python.org/) and [Bash](https://en.wikipedia.org/wiki/Bash_%28Unix_shell%29) scripts, and is not friendly for those not familiar with such an approach.
* The codebase and technical documentation are maintained on our [GitHub repository](https://github.com/eegsynth/eegsynth). It is strongly advised to work within you own cloned repository and keep up to date with EEGsynth commits, as the EEGsynth is in constant development.
* For installation please follow our installation instructions for [Linux](https://github.com/eegsynth/eegsynth/blob/master/doc/installation-linux.md), [OSX](https://github.com/eegsynth/eegsynth/blob/master/doc/installation-osx.md) and [Windows](https://github.com/eegsynth/eegsynth/blob/master/doc/installation-windows.md). Please note that Windows and OSX are not actively supported. Linux is the main target, partly because we want the EEGsynth to be compatible with the [Raspberry Pi](http://raspberrypi.org/), partly because some Python libraries do not support Windows, and partly because we rely on command-line interface anyway.
* The EEGsynth was initiated by the art-science collective [1+1=3](http://oneplusoneisthree.org/) who uses the EEGsynth for its performances and workshops.
* The EEGsynth is used in the [COGITO](http://www.cogitoinspace.org/) project to transform 32-channel EEG into sound for realtime transmission by a 25-meter radiotelescope.
* The EEGsynth project is non-commercial and developed by us in our own time. We are grateful to have received financial support from [Innovativ Kultur](http://www.innovativkultur.se/), [The Swedish Arts Grant Council](http://www.kulturradet.se/en/in-english/), [Kulturbryggan](http://www.konstnarsnamnden.se/default.aspx?id=18477) and [Stockholm County Council](http://www.sll.se/om-landstinget/Information-in-English1/).
* You read our [news blog](http://www.eegsynth.org/?page_id=621), follow us on [Facebook](https://www.facebook.com/EEGsynth/) and [Twitter](https://twitter.com/eegsynth), and check our past and upcoming events on [our calendar](http://www.eegsynth.org/?calendar=eegsynth-calendar).
* Please feel free to contact us with questions and ideas for collaborations via our [contact form](http://www.eegsynth.org/?page_id=233).

## Modular design

The EEGsynth is a collection of separate modules, directly inspired by  [modular synthesizers](https://en.wikipedia.org/wiki/Modular_synthesizer) (see picture below). Similarly as in a modular synthesizers, simple software modules (python scripts) are connected, or “patched”, to create complex and flexible behavior. Each module runs in parallel, performing a particular function. For example, imagine module **A** is responsible for determining the heart-rate from ECG (voltages from the heart), while module **B** sends out a signal to a drummachine a every _n_ milliseconds. By patching **A&rightarrow;B**, the EEGsynth can be made to control a drum-machine at the speed of the heart rate.

![Example of complex modular synthesizer patch](http://www.modcan.com/mainImages/bphoto/bigA.jpg "Example of complex modular synthesizer patch")

**Figure 1.** *Example of complex modular synthesizer patch*

## Patching 

In the EEGsynth patching (communication) between modules is implemented through the use of the open-source [Redis database](http://Redis.io/) which stores [attribute-value pairs](https://en.wikipedia.org/wiki/Attribute%E2%80%93value_pair). Attribute-value pairs are nothing more than an attribute name with a value assigned to it, such as ('Name', 'John') or ('Height', 1.82). A module can put anything it wants into the database, such as ('Heartrate', 92). Another module can ask the database to return the value belonging to ('Heartrate'). This allows one to create complex, many-to-many patches. Interactions with Redis are specified separately for each module in their own* .ini* file (initialization file). The *.ini* file is a text file with human-understandable formatting (according to Python’s [ConfigParser class](https://docs.python.org/2/library/configparser.html)) where we define the attribute names that are used for input and output. For example, here we have [*spectral.ini*](https://github.com/eegsynth/eegsynth/modules/spectral/spectral.ini):

```
[general]
debug=2
delay=0.1

[Redis]
hostname=localhost
port=6379

[fieldtrip]
hostname=localhost
port=1972
timeout=30

[input]
; the channel names can be specifies as you like
; you should give the hardware channel indices
channel1=1
channel2=2
channel3=3
channel4=4
channel5=5
channel6=6
;frontal=1
;occipital=2

[processing]
; the sliding window is specified in seconds
window=2.0

[band]
; the frequency bands can be specified as you like, but must be all lower-case
; you should give the lower and upper range of each band
delta=2-5
theta=5-8
alpha=9-11
beta=15-25
gamma=35-45
; it is also possible to specify the range using control values from Redis
redband=plotsignal.redband.lo-plotsignal.redband.hi
blueband=plotsignal.blueband.lo-plotsignal.blueband.hi

[output]
; the results will be written to Redis as "spectral.channel1.alpha" etc.
prefix=spectral
```

The spectral module calculates the spectral power in different frequency bands. Those frequency bands, and their name, are given in the .ini file. As you can see some are defined by numbers ('alpha=9-11'), while others use Redis keys ('redband=plotsignal.redband.lo - plotsignal.redband.hi'). In the latter case, the frequency band is determined (via Redis) by the plotsignal module, which can be used to visually select frequency bands. The spectral module also outputs (power) values to Redis, prefixed by 'spectral' (see [output] in the .ini file above).

As you can see, the .ini file includes other settings as well. You can find a default .ini in their respective directory, with a filename identical to the module. E.g. [module/spectral](https://github.com/eegsynth/eegsynth/tree/master/module/spectral) contains [spectral.py](https://github.com/eegsynth/eegsynth/tree/master/module/spectral/spectral.py) and [spectral.ini](https://github.com/eegsynth/eegsynth/tree/master/module/spectral/spectral.ini). Initialization files can be edited with any text editor but should be saved in a separate 'patch directory', in which you store all the .ini files belonging to one patch. This helps organizing your patches as well as your local git repository, which will then not create conflicts with the remote default .ini files.

## Data acquisition and communication
The EEGsynth uses the FieldTrip buffer to exchange eletrophysiological data between modules. It is the place where raw (or processed) data is stored and updated with new incoming data. For more information on the FieldTrip buffer, check the [FieldTrip documentation](http://www.fieldtriptoolbox.org/development/realtime/buffer). Note that the FieldTtrip buffer allows parallel reading of data. Some modules, such as the *spectral* module, take data from the FieldTrip buffer as input and output values to the Redis buffer. Other modules take care of the data acquisition, interfacing with acquisition devices and updating the FieldTrip buffer with incoming data.  We typically use the affordable open-source hardware of the [OpenBCI ](http://openbci.org/) project for electrophysiological recordings. However,  EEGsynth can also interface with other state-of-the-art commercial devices using FieldTrip's [device implementations](http://www.fieldtriptoolbox.org/development/realtime/implementation).

## Controlling external software and hardware
The purpose of the EEGsynth is to control exernal software and hardware with electrophysiological signals. Originally developed to control modular synthesizers, the EEGsynth supports most protocols for sound synthesis and control, such as [CV/gate](https://en.wikipedia.org/wiki/CV/gate), [MIDI](https://www.midi.org/), [Open Sound Control](http://opensoundcontrol.org/introduction-osc), [DMX512](https://en.wikipedia.org/wiki/DMX512) and [Art-Net](https://en.wikipedia.org/wiki/Art-Net). These modules are prefixed with 'output' and output values and events from Redis to its protocol. Redis can also be accessed directly, e.g. in games using [PyGame](https://www.pygame.org/news). Rather than interfacing with music hardware, output to [Open Sound Control](http://opensoundcontrol.org/introduction-osc) can be used to control music software such as the remarkable open-source software [Pure Data](https://puredata.info/), for which one can find [many applications](https://patchstorage.com/platform/pd-extended/) in music, art, games and science.

## Manual control
Although the purpose of the EEGsynth (and BCIs in general) is to control devices using biological signals, some manual interaction might be desired, e.g. to adjust the dynamics of the output or to select the frequency range of the brainsignal during the recording. However, as with analogue synthsizers, we like the tactile real-time aspect of knobs and buttons, but would like to avoid using a computer keyboard. We therefor mainly use MIDI controllers, such as the [LaunchControl XL](https://global.novationmusic.com/launch/launch-control-xl#) displayed below. Identical to all other modules, the launchcontrol *module* records the launchcontrol input from sliders, knobs, and buttons into the Redis database to be used by other modules.

![](https://novationmusic.com/sites/novation/files/LCXL-HeaderImage-2560-1000.png)

**Figure 2.** *The Novation LaunchControl XL, often used in EEGsynth setups*

## Summary
To summarize, the EEGsynth is an open-source code-base that functions as an interface between electrophysiological recordings devices and external software and devices. It takes care for the analyis of data on the one hand, and the translation into external protocols on the other. This is done in a powerful, flexible way, by running separate modules in parallel. These modules exchange data and parameters using the FieldTrip buffer and Redis database, respectively. This 'patching' is defined using text-based initialization files of each module. The EEGsynth is run from the command-line, without a GUI and without visual feedback (except for the plotting modules), and interaction using MIDI controllers, rather than computer keyboards. The upside is that the EEGsynth is easily customized and expanded, has the true feel and fucntion of a real-time feedback system, and can be light enough to run e.g. on a Raspberry-Pi (i.e. on Raspian). Below you can see the current (actually, already outdated) collection of modules included in the EEGsynth, showing the two different ways of communication: via the FieldTrip bugger (data) and via Redis (control values and parameters).

[![](http://www.eegsynth.org/wp-content/uploads/2016/08/EEGsynth_comm_overview-1024x576.jpg?resize=1024%2C576)](http://www.eegsynth.org/wp-content/uploads/2016/08/EEGsynth_comm_overview-1024x576.jpg)

**Figure 3.** *Visual depiction of communication between modules via either the FieldTrip buffer for raw data (yellow) or via the Redis database (blue) for output and input parameters.*
