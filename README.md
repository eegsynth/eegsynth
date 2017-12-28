# The EEGsynth

## Table of contents
* [Background](#user-content-background)
* [Introduction](#user-content-introduction)
  * [Modular design and patching](#user-content-modular-design-and-patching)
  * [Data acquisition and communication](#user-content-data-acquisition-and-communication)
  * [Controlling external software and hardware](#user-content-controlling-external-software-and-hardware)
  * [Manual control](#user-content-manual-control)
  * [Summary](#user-content-summary)
* [Module overview](#user-content-module-overview)
* [Tutorials](#user-content-tutorials)
  * [Tutorial 1: Playback data, and display on monitor](#user-content-tutorial-1--playback-data--and–display-on-monitor)
  * [Tutorial 2: using Redis for live interaction with modules](#user-content-tutorial-2--using-redis-for-live-interaction-with-modules)
  * [Tutorial 3: Real-time EEG recording with OpenBCI](#user-content-tutorial-3--real-time-eeg-recording-with-openbci)

# Background
The EEGsynth is an open-source [Python](https://www.python.org/) codebase that provides a real-time interface between (open-hardware) devices for electrophysiological recordings (e.g. EEG, EMG and ECG) and analogue and digital devices (e.g. MIDI, games and analogue synthesizers). This allows one to use electrical brain/body activity to flexibly control devices in real-time, for what are called (re)active and passive brain-computer-interfaces (BCIs), biofeedback and neurofeedback. The EEGsynth does *not* allow diagnostics, and neither does it provide a GUI for offline analysis. Rather, the EEGsynth is intended as a collaborative interdisciplinary [open-source](https://opensource.com/open-source-way) and [open-hardware](https://opensource.com/resources/what-open-hardware) project that brings together programmers, musicians, artists, neuroscientists and developers for scientific and artistic exploration.

* The EEGsynth is intended to be run from the command line, using [Python](https://www.python.org/) and [Bash](https://en.wikipedia.org/wiki/Bash_%28Unix_shell%29) scripts, and is not friendly for those not familiar with such an approach.
* The codebase and technical documentation are maintained on our [GitHub repository](https://github.com/eegsynth/eegsynth). It is strongly advised to work within you own cloned repository and keep up to date with EEGsynth commits, as the EEGsynth is in constant development.
* For installation please follow our installation instructions for [Linux](https://github.com/eegsynth/eegsynth/blob/master/doc/installation-linux.md), [OSX](https://github.com/eegsynth/eegsynth/blob/master/doc/installation-osx.md) and [Windows](https://github.com/eegsynth/eegsynth/blob/master/doc/installation-windows.md). Please note that Windows and OSX are not actively supported. Linux is the main target, partly because we want the EEGsynth to be compatible with the Raspberry-Pi, partly because some Python libraries do not support Windows, and partly because we rely on command-line interface anyway.
* Preliminary didactic material can be found on our [wiki page](https://braincontrolclub.miraheze.org/wiki/Main_Page) of the Brain Control Club, a student club at [Center for Research and Interdisciplinarity (CRI)](https://cri-paris.org/).
* You can watch a recent [presentation](http://medias.ircam.fr/stream/int/video/files/2017/07/12/StephenWhitmarsh.mov.webm) on the inspiration for the EEGsynth in the commonalities between between brain (activity) and sound (waves) at [IRCAM](https://www.ircam.fr/).
* The EEGsynth was initiated and still used artistic performances and workshops by the art-science collective [1+1=3](http://oneplusoneisthree.org/).
* The EEGsynth is used in the [COGITO](http://www.cogitoinspace.org/) project to transform 32-channel EEG into sound for realtime transmission by a 25-meter radiotelescope.
* The EEGsynth project is non-commercial and developed by us in our own time. We are grateful to have received financial support from [Innovativ Kultur](http://www.innovativkultur.se/), [The Swedish Arts Grant Council](http://www.kulturradet.se/en/in-english/), [Kulturbryggan](http://www.konstnarsnamnden.se/default.aspx?id=18477) and [Stockholm County Council](http://www.sll.se/om-landstinget/Information-in-English1/).
* You can follow us on [Facebook](https://www.facebook.com/EEGsynth/) and [Twitter](https://twitter.com/eegsynth), read our [news blog](http://www.eegsynth.org/?page_id=621), and check our past and upcoming events on [our calendar](http://www.eegsynth.org/?calendar=eegsynth-calendar).
* Please feel free to contact us with questions and ideas for collaborations via our [contact form](http://www.eegsynth.org/?page_id=233).

# Introduction
What follows is a short introduction on the design and use of the EEGsynth. This is followed by tutorials to get you started creating your own BCI system.

## Modular design and patching

The EEGsynth is a collection of separate modules, directly inspired by  [modular synthesizers](https://en.wikipedia.org/wiki/Modular_synthesizer) (see picture below). Similarly as in a modular synthesizers, simple software modules (python scripts) are connected, or “patched”, to create complex and flexible behavior. Each module runs in parallel, performing a particular function. For example, imagine module **A** is responsible for determining the heart-rate from ECG (voltages from the heart), while module **B** sends out a signal to a drummachine a every _n_ milliseconds. By patching **A&rightarrow;B**, the EEGsynth can be made to control a drum-machine at the speed of the heart rate.

![Example of complex modular synthesizer patch](http://www.modcan.com/mainImages/bphoto/bigA.jpg "Example of complex modular synthesizer patch")

**Figure 1.** *Example of complex modular synthesizer patch*


In the EEGsynth patching is implemented through the use of the open-source [Redis database](http://redis.io/) which stores [attribute-value pairs](https://en.wikipedia.org/wiki/Attribute%E2%80%93value_pair). Attribute-value pairs are nothing more than an attribute name with a value assigned to it, such as ('Name', 'John') or ('Height', 1.82). A module can put anything it wants into the database, such as ('Heartrate', 92). Another module can ask the database to return the value belonging to ('Heartrate'). This allows one to create complex, many-to-many patches. Interactions with Redis are specified separately for each module in their own* .ini* file (initialization file). The *.ini* file is a text file with human-understandable formatting (according to Python’s [ConfigParser class](https://docs.python.org/2/library/configparser.html)) where we define the attribute names that are used for input and output. For example, here we have [*spectral.ini*](https://github.com/eegsynth/eegsynth/modules/spectral/spectral.ini):

```
[general]
debug=2
delay=0.1

[redis]
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
; it is also possible to specify the range using control values from redis
redband=plotsignal.redband.lo-plotsignal.redband.hi
blueband=plotsignal.blueband.lo-plotsignal.blueband.hi

[output]
; the results will be written to redis as "spectral.channel1.alpha" etc.
prefix=spectral
```

The spectral module calculates the spectral power in different frequency bands. Those frequency bands, and their name, are given in the .ini file. As you can see some are defined by numbers ('alpha=9-11'), while others use Redis keys ('redband=plotsignal.redband.lo-plotsignal.redband.hi'). In the latter case, the frequency band is determined (via Redis) by the plotsignal module, which can be used to visually select frequency bands. In its turn, the spectral module outputs (power) values to Redis, prefixed by 'spectral' (see its output field).

As you can see, the .ini file includes other settings as well. You can find a default .ini in their respective directory, with a filename identical to the module. E.g. [module/spectral](https://github.com/eegsynth/eegsynth/tree/master/module/spectral) contains [spectral.py](https://github.com/eegsynth/eegsynth/tree/master/module/spectral/spectral.py) and [spectral.ini](https://github.com/eegsynth/eegsynth/tree/master/module/spectral/spectral.ini). Initialization files can be edited with any text editor but should be saved in a separate 'patch directory', in which you store all the .ini files belonging to one patch. This helps organizing your patches as well as your local git repository, which will then not create conflicts with the remote default .ini files.

## Data acquisition and communication
The EEGsynth uses the FieldTrip buffer to exchange eletrophysiological data between modules. It is the place where raw (or processed) data is stored and updated with new incoming data. For more information on the FieldTrip buffer, check the [FieldTrip documentation](http://www.fieldtriptoolbox.org/development/realtime/buffer). Note that the FieldTtrip buffer allows parallel reading of data. Some modules, such as the *spectral* module, take data from the FieldTrip buffer as input and output values to the Redis buffer. Other modules take care of the data acquisition, interfacing with acquisition devices and updating the FieldTrip buffer with incoming data.  We typically use the affordable open-source hardware of the [OpenBCI ](http://openbci.org/) project for electrophysiological recordings. However,  EEGsynth can also interface with other state-of-the-art commercial devices using FieldTrip's [device implementations](http://www.fieldtriptoolbox.org/development/realtime/implementation).

## Controlling external software and hardware
The purpose of the EEGsynth is to control exernal software and hardware with electrophysiological signals. Originally developed to control modular synthesizers, the EEGsynth supports most protocols for sound synthesis and control, such as [CV/gate](https://en.wikipedia.org/wiki/CV/gate), [MIDI](https://www.midi.org/), [Open Sound Control](http://opensoundcontrol.org/introduction-osc), [DMX512](https://en.wikipedia.org/wiki/DMX512) and [Art-Net](https://en.wikipedia.org/wiki/Art-Net). These modules are prefixed with 'output' and output values and events from Redis to its protocol. Redis can also be accessed directly, e.g. in games using [PyGame](https://www.pygame.org/news). Rather than interfacing with music hardware, output to [Open Sound Control](http://opensoundcontrol.org/introduction-osc) can be used to control music software such as the remarkable open-source software [Pure Data](https://puredata.info/), for which one can find [many applications](https://patchstorage.com/platform/pd-extended/) in music, art, games and science.

## Manual control
Although the purpose of the EEGsynth (and BCIs in general) is to control devices using biological signals, some manual interaction might be desired, e.g. to adjust the dynamics of the output or to select the frequency range of the brainsignal during the recording. However, as with analogue synthsizers, we like the tactile real-time aspect of knobs and buttons, but would like to avoid using a computer keyboard. We therefor mainly use MIDI controllers, such as the [LaunchControl XL](https://global.novationmusic.com/launch/launch-control-xl#) displayed below. Identical to all other modules, the launchcontrol *module* records the launchcontrol input from sliders, knobs, and buttons into the Redis database to be used by other modules.

![](https://d2xhy469pqj8rc.cloudfront.net/sites/default/files/styles/cta_scale_640/public/news_images/LCXL101_Thumb.jpg?itok=_gwQDWQi)

**Figure 2.** *The Novation LaunchControl XL, often used in EEGsynth setups*

## Summary
To summarize, the EEGsynth is an open-source code-base that functions as an interface between electrophysiological recordings devices and external software and devices. It takes care for the analyis of data on the one hand, and the translation into external protocols on the other. This is done in a powerful, flexible way, by running separate modules in parallel. These modules exchange data and parameters using the FieldTrip buffer and Redis database, respectively. This 'patching' is defined using text-based initialization files of each module. The EEGsynth is run from the command-line, without a GUI and without visual feedback (except for the plotting modules), and interaction using MIDI controllers, rather than computer keyboards. The upside is that the EEGsynth is easily customized and expanded, has the true feel and fucntion of a real-time feedback system, and can be light enough to run e.g. on a Raspberry-Pi (i.e. on Raspian). Below you can see the current (actually, already outdated) collection of modules included in the EEGsynth, showing the two different ways of communication: via the FieldTrip bugger (data) and via Redis (control values and parameters).

[![](http://i0.wp.com/www.ouunpo.com/eegsynth/wp-content/uploads/2016/08/EEGsynth_comm_overview-1024x576.jpg?resize=1024%2C576)](http://i1.wp.com/www.ouunpo.com/eegsynth/wp-content/uploads/2016/08/EEGsynth_comm_overview.jpg)

**Figure 3.** *Visual depiction of communication between modules via either the FieldTrip buffer for raw data (yellow) or via the Redis database (blue) for output and input parameters.*

# Module overview
Detailed information about each module can be found in the README.md included in each module directory. Here follows a description of the current available modules.

### Analysis

* [Spectral](https://github.com/eegsynth/eegsynth/tree/master/module/spectral) Analyzes power in frequency bands in the raw data buffer
* [Muscle](https://github.com/eegsynth/eegsynth/tree/master/module/muscle) Calculates RMS from EMG recordings in the raw data buffer
* [Accelerometer](https://github.com/eegsynth/eegsynth/tree/master/module/accelerometer) Extracts accelerometer data (X,Y,Z) from onboard sensor of the OpenBCI  in the raw data buffer
* [EyeBlink](https://github.com/eegsynth/eegsynth/tree/master/module/eyeblink) Detects eye blinks in the raw data buffer
* [HeartRate](https://github.com/eegsynth/eegsynth/tree/master/module/heartrate) Extracts heart rate in the raw data buffer

### Data acquisition

* [Openbci2ft](https://github.com/eegsynth/eegsynth/tree/master/module/openbci2ft) Records raw data from the OpenBCI amplifier and places it in the buffer.
* [Jaga2ft](https://github.com/eegsynth/eegsynth/tree/master/module/jaga2ft) Records raw data from Jaga amplifier and places it in the buffer
* For more supported acquisition devices [look here](http://www.fieldtriptoolbox.org/development/realtime/implementation)

### Communication between modules

* [Redis](https://github.com/eegsynth/eegsynth/tree/master/module/redis) The database for communicating data between modules
* [Buffer](https://github.com/eegsynth/eegsynth/tree/master/module/buffer) FieldTrip buffer for communicating raw data

### Utilities for optimizing data flow, patching and prototyping

* [Playbacksignal](https://github.com/eegsynth/eegsynth/tree/master/module/playbacksignal) Play back pre-recorded raw data
* [Plotsignal ](https://github.com/eegsynth/eegsynth/tree/master/module/plotsignal)Plot raw data and frequency decomposition in real-time
* [Playbackcontrol ](https://github.com/eegsynth/eegsynth/tree/master/module/playbackcontrol)Playback control values
* [Plotcontrol ](https://github.com/eegsynth/eegsynth/tree/master/module/plotcontrol) Plot control signals from Redis, and calibrates them to values 0-1.
* [Postprocessing](https://github.com/eegsynth/eegsynth/tree/master/module/postprocessor) Allows computations, algorithms and combinations on the data (output from modules)
* [Preprocessing](https://github.com/eegsynth/eegsynth/tree/master/module/preprocessor) Preprocess raw data, and places it in new raw data buffer

### External interfaces (open-source)

* [OutputAudio ](https://github.com/eegsynth/eegsynth/tree/master/module/outputaudio)Send (sound) to soundcard
* [InputOSC](https://github.com/eegsynth/eegsynth/tree/master/module/inputosc) Receive data from [Open Sound Control](http://opensoundcontrol.org/introduction-osc) protocol
* [OutputOSC](https://github.com/eegsynth/eegsynth/tree/master/module/outputosc) Send data via [Open Sound Control](http://opensoundcontrol.org/introduction-osc) protocol
* [OutputArtNet ](https://github.com/eegsynth/eegsynth/tree/master/module/outputartnet)Send data according to [Art-Net protocol](https://en.wikipedia.org/wiki/Art-Net)
* [OutputDMX ](https://github.com/eegsynth/eegsynth/tree/master/module/outputdmx512)Send data according to [DMX512 protocol](https://en.wikipedia.org/wiki/DMX512)
* [OutputCVgate](https://github.com/eegsynth/eegsynth/tree/master/module/outputcvgate) Send continuous voltages for interfacing with analogue synthesizers using [our own hardware](http://www.ouunpo.com/eegsynth/?page_id=516)
* [InputMIDI ](https://github.com/eegsynth/eegsynth/tree/master/module/inputmidi)Receive MIDI signals

### External interfaces (consumer)

* [LaunchControl](https://github.com/eegsynth/eegsynth/tree/master/module/launchcontrol) Records and send data to the Novation[ LaunchControl XL MIDI controller](https://global.novationmusic.com/launch/launch-control-xl)
* [LaunchPad ](https://github.com/eegsynth/eegsynth/tree/master/module/launchpad)Record and send data to the Novation [Launchpad MIDI controller](https://global.novationmusic.com/launch/launchpad)
* [VolcaBass](https://github.com/eegsynth/eegsynth/tree/master/module/volcabass) Interface with the Korg [Volca Bass](http://www.korg.com/us/products/dj/volca_bass/) synthesizer
* [VolcaBeats](https://github.com/eegsynth/eegsynth/tree/master/module/volcabeats) Interface with the Korg [Volca Beats](http://www.korg.com/us/products/dj/volca_beats/) synthesizer
* [VolcaKeys](https://github.com/eegsynth/eegsynth/tree/master/module/volcakeys) Interface with the Korg [Volca Keys](http://www.korg.com/us/products/dj/volca_keys/) synthesizer
* [AVmixer ](https://github.com/eegsynth/eegsynth/tree/master/module/avmixer)Interface with [NeuroMixer AVmixer](https://neuromixer.com/) software for control of video presentations
* [Endorphines ](https://github.com/eegsynth/eegsynth/tree/master/module/endorphines)Interface with Endorphines’ [Shuttle Control ](https://endorphin.es/endorphin.es--modules.html)MIDI to CV module
* [Keyboard](https://github.com/eegsynth/eegsynth/tree/master/module/keyboard) Records MIDI keyboard note and velocity input

### Software synthesizer modules

* [Pulsegenerator](https://github.com/eegsynth/eegsynth/tree/master/module/pulsegenerator) Send pulses, i.e. for gates, or MIDI events synchronized with heart beats
* [Sequencer](https://github.com/eegsynth/eegsynth/tree/master/module/sequencer) A basis sequencer to send out sequences of notes
* [Synthesizer](https://github.com/eegsynth/eegsynth/tree/master/module/synthesizer) A basic synthesizer to send our waveforms
* [Quantizer ](https://github.com/eegsynth/eegsynth/tree/master/module/quantizer)Quantize output chromatically or according to musical scales

### COGITO project

* [Cogito](https://github.com/eegsynth/eegsynth/tree/master/module/cogito) Streaming EEG data (from the Gtec EEG) to audio for radio transmission, using our interstellar protocol

# Tutorials

## Tutorial 1: Playback data, and display on monitor

We will start with the following setup wherein we will playback data to the buffer as if it is recorded in real-time. This is convenient, since it will allow you to develop and test your BCI without having to rely on real-time recordings.

[![](https://static.miraheze.org/braincontrolclubwiki/6/61/Tutorial1.png)](https://braincontrolclub.miraheze.org/wiki/File:Tutorial1.png)  

Boxes depict EEGsynth modules. Orange arrows describe time-series data. Blue arrows describe Redis data

### Starting the data buffer

The EEGsynth uses the FieldTrip buffer to communicate data between modules. It is the place where raw (or processed) data is stored and updated with new incoming data. For more information on the FieldTrip buffer, check the [FieldTrip documentation](http://www.fieldtriptoolbox.org/development/realtime/buffer).

1.   Navigate to the buffer module directory _/eegsynth/module/buffer_
2.   Copy the _buffer.ini_ to your own ini directory (e.g. to _/eegsynth/inifiles_, which would be in _../../inifiles_ relative to the buffer module directory)
3.   Start up the buffer module, using your own ini file: _./buffer.sh -i ../../inifiles/launchcontrol.ini_. Note here that the buffer module is one of the few modules that are an executable written in C, run from a bash script rather than Python. However, it does function exactly the same concerning the user-specific ini files.
4.   If the buffer module is running correctly, it does not print any feedback in the terminal. So no news is good news!

### Writing pre-recorded data from HDD to the buffer

We will then write some prerecorded data into the buffer as if it was being recorded in real-time:

1.   Download some example data in .edf format. For example, from our [data directory on Google Drive](https://drive.google.com/drive/folders/0B10S8PeNnxw1ZnZPbUh0RWk0cjA). Or use the data you recording in the [recording tutorial](https://braincontrolclub.miraheze.org/wiki/Recording_tutorial "Recording tutorial").
2.   Place the .edf file in a directory, e.g. in _/eegsynth/datafiles_
3.   Navigate to the playback module directory _/eegsynth/module/playback_
4.   Copy the _playback.ini_ to your own ini directory (e.g. to _/eegsynth/inifiles_, which would be in _../../inifiles_ relative to the buffer module directory)
5.   Edit your _playback.ini_ to direct the playback module to the right edf data file, e.g. under _[playback]_ edit: _file = ../../datafiles/testBipolar20170827-0.edf_
6.   Edit the two _playback.ini_ options for playback and rewind so that it will play back automatically (and not rewind): _play=1_ and _rewind=0_
7.   Make note that you can comment out (hide from the module) lines of text by adding a semicolon (;) at the beginning of the line
8.   Now start up the playback module, using your own .ini file: _python playback.py -i ../../inifiles/playback.ini_
9.   If all is well, the module will print out the samples that it is 'playing back'. This is that data that is successively entered into the buffer as if was just recorded

### Plotting streaming data in the buffer

If you made it so far the buffer is working. However, we can now also read from the buffer and visualize the data as it comes in, using the plotsignal module. Note you need to be in a graphical environment for this.

1.   Navigate to the plotsignal module directory _/eegsynth/module/plotsignal_
2.   Copy the _plotsignal.ini_ to your own ini directory (e.g. to _/eegsynth/inifiles_, which would be in _../../inifiles_ relative to the buffer module directory)
3.   Edit your _plotsignal.ini_ to plot the first two channel, but editing under _[arguments]_ edit: _channels=1,2_
4.   Now start up the plotsignal module, using your own .ini file: _python plotsignal.py -i ../../inifiles/plotsignal.ini_
5.   If you see your data scroll by, bravo!

## Tutorial 2: using Redis for live interaction with modules

Now we have set up a basic minimal pipe-line with data transfer, we can introduce communication between modules used the Redis database. Redis is the place where modules communicate via 'key-value' pairs. Read the [online documentation](http://www.ouunpo.com/eegsynth/?page_id=514) on the EEGsynth website for more background on the use of Redis. In this tutorial we will influence the behavior of the plotsignal output module, by changing parameters in Redis, while having the plotsignal module use these parameters as well as writing parameters back in Redis. It becomes important now to really understand the flow of information in the schema.

[![](https://static.miraheze.org/braincontrolclubwiki/3/30/Tutorial2.png)](https://braincontrolclub.miraheze.org/wiki/File:Tutorial2.png)  

Boxes depict EEGsynth modules. Orange arrows describe time-series data. Blue arrows describe Redis data

### Writing and reading from Redis

After installation of the EEGsynth, the Redis database should be running in the background at startup. To check whether Redis is working you can monitor Redis while adding and reading 'key-value' pairs. For the purpose of the tutorial we will use the LaunchControl MIDI controller to enter values from the LaunchControl to Redis. If you do not have a Launchcontrol, you can enter values by hand. We will discuss this as well (just skip this part).

1.   Navigate to launchcontrol module directory _/eegsynth/module/launchcontrol_
2.   Copy the _launchcontrol.ini_ to your own ini directory (e.g. to _/eegsynth/inifiles_, which would be in _../../inifiles_ relative to the launchcontrol module directory)
3.   Start up the launchcontrol module, using your own ini file: _python launchcontrol.py -i ../../inifiles/launchcontrol.ini_
4.   You will see the connected MIDI devices printed in the terminal. If you have not set up the .ini file correctly yet, read out the MIDI device name from the output, and replace the device name, e.g. _device=Launch Control_ under the _[midi]_ field of your .ini file.
5.   Now restart the launchcontrol module. If everything is working correctly, a move of any of the sliders will print a key-value pair in the terminal.

You can also add values to Redis directly in Python:

1.   Start up Python, i.e. type _python_ in the terminal
2.   Import Redis, i.e. type _import r as redis_
3.   Set a key-value pair, by typing _r.set('test_key','10')_
4.   Read a key-value pair, by typing _r.set('test_key')_

### Patching the plotsignal module

You can now monitor the actions of Redis by opening a new terminal window and running _redis-cli monitor_. You should be able to see both _set_ and _get_ actions. So monitor this window while adding values in Redis as described above to see if it is working correctly. If you are using the launchcontrol module, you will see that the keys will be named something like _launchcontrol.control077_. We can tell the plotvisual module to use these values to adapt its behaviour. It will then take these values and relate them to the range of its spectral analysis, to determine frequency bands of its 'red band' and 'blue band'. The plotvisual module, in its turn, will output these frequency bands back into Redis. This makes them available to e.g. further EEG analysis. Take a moment to consider this pipeline. We call this connecting of modules via Redis parameters 'patching', referring to patching in modular synthesizers.

1.   Determine which launchcontrol sliders/rotators you want to use by moving them and looking at the values that change in Redis (use _redis-cli monitor_). Let's say we will do the following:

    * _launchcontrol.control013_ will determine the center frequency of red band
    * _launchcontrol.control029_ will determine the half-width of red band
    * _launchcontrol.control014_ will determine the center frequency of blue band
    * _launchcontrol.control030_ will determine the half-width of blue band

2.   Now edit your _plotsignal.ini_ file to enter these as parameters as follows under _[input]_:

    * _redfreq=launchcontrol.control013_
    * _redwidth=launchcontrol.control029_
    * _bluefreq=launchcontrol.control014_
    * _bluewidth=launchcontrol.control030_

The plotsignal module will now look into Redis to try to find values there corresponding to the status of these keys. If you now change the value of any of these key-value pairs by e.g. rotating a button, the LaunchControl module will update these values in Redis, where the plotsignal module will read them and adjust its display (the red and blue lines delineating the two frequency bands). You can now move the frequency bands around, and get visual feedback overlayed on the spectrum of the channels that you are plotting. The plotsignal module also makes a conversion between the state of the values it reads from Redis (the last read position of the knobs), to frequencies in Hertz. It outputs those back into Redis, e.g. under _plotsignal.redband.lo_, and _plotsignal.redband.hi_. You can check this by using _redis-cli monitor_.

## Tutorial 3: Real-time EEG recording with OpenBCI

Now we have set up a basic pipeline, we can replace the playback of EEG with real-time recordings of EEG. The EEGsynth supports many EEG devices, thanks to fact that we use FieldTrip's support of EEG devices in its real-time development. Read the [FieldTrip realtime development documentation](http://www.fieldtriptoolbox.org/development/realtime/implementation) for more information. We only distribute OpenBCI, Jaga and GTec devices with the EEGsynth (and not all their devices yet). These modules (e.g. openbci2ft, jaga2ft and gtec2ft) are written in C, because they rely on very specific interfacing with their devices and software. However, we use them as we would any other module, i.e. start them up with a user-specified .ini file. Similarly as the playback module, these write to the buffer. They do this typically in blocks of data that are relatively small number of samples compared to the time  we use to analyse the data and control devices.

[![](https://static.miraheze.org/braincontrolclubwiki/4/4f/Tutorial3.png)](https://braincontrolclub.miraheze.org/wiki/File:Tutorial3.png)  

Boxes depict EEGsynth modules. Orange arrows describe time-series data. Blue arrows describe Redis data

### Setting up EEG recording

The most important lesson here is actually how to set up proper EEG recordings, but this falls outside of the scope of this tutorial. Please refer to our [recording tutorial](https://braincontrolclub.miraheze.org/wiki/Recording_tutorial "Recording tutorial") to familiarize yourself with the recording procedure first. When you did so, and got some experience (best is to do so under supervision of a more experienced EEG user), we will patch the EEG real-time recording in the pipeline of the previous tutorial, replacing the playback module with the openbci2ft module. If you are using another device, the principle will be the same.

1.   Navigate to openbci2ftmodule directory _/eegsynth/module/openbci2ft_
2.   Copy the _openbci2ft.ini_ to your own ini directory (e.g. to _/eegsynth/inifiles_, which would be in _../../inifiles_ relative to the openbci2ftmodule directory)
3.   We will need to plug in the OpenBCI dongle into a USB port. But before you do so, do the following:

    1.   Open a new terminal window and list the devices of the kernel, by typing _ls /dev_.
    2.   Plug in the OpenBCI dongle in a USB port
    3.   List the device again using _ls /dev_
    4.   If you compare the two lists, you should see that another device was added after you plugged in the dongle. It will probably start with _ttyUSB_ followed with a number. This is the USB port number at which the dongle is connected. If you unplug or restart your computer, this number might change, and therefor you will probably need to do this check regularly. There might be easier ways of finding the USB port number, but this, at least, is fool-proof.

4.   Edit your openbci2ft.ini file and enter the right port name for the dongle, which you can find under [General], e.g _serial = /dev/ttyUSB1_
5.   Start up the openbci2ft module, using your own ini file: _python openbci2ft.py -i ../../inifiles/openbci2ft.ini_. If things are working, you the terminal will print a message that it is waiting to connect.
6.   You can now turn on the EEG board (not the dongle) by moving the little switch to either side. After a couple of second you should see the dongle starting to blink a green and red light. This means it is configuring the EEG board with the settings specified in the .ini file, which will take a couple of seconds. After that you should have your data coming in, being transferred into the fieldtrip buffer.
7.   Now you can check the incoming data with the plotsignal module.
