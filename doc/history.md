# A brief history

Early development of what later became the EEGsynth was done as part of an interdisciplinary art-science 
initiative [1+1=3](http://oneplusoneisthree.org/), which was on its part a spin-off of a successful international art-research collective
[OuUnPo](http://www.ouunpo.org/). After years of intermittent performances and workshops within 
[OuUnPo](http://www.ouunpo.org/), some of us we were in need of a more concrete and continuous method of exploring a diversity of 
research practices within overlapping themes including neuroscience, music and performance. In November 2014 we first 
used EEG brain activity (of an actor reading a piece by Samuel Beckett) in a performance by transforming it into a score 
for two actors, [staged at the SP Escola de Teatro](http://www.eegsynth.org/?p=51), in Sao Paulo, Brazil.
This proved inspirng, and we started writing some early [MATLAB] code, using FieldTrip's architecture and functions for realtime EEG processing. 
We acquired our own [OpenBCI](https://openbci.com/) board (now the Cyton board), which Robert Oostenveld and Stefan Debener 
then implemented in FieldTrip. Artistically, we developed our ideas around providing feedback using sound within 
performative art, especially dance, using electomyography (the measurment of electrical 
signals in muscular control), together with dancer and choreographer [Carima Neusser](http://www.carimaneusser.com/).
This resulted in our first EEGsynth performance in Stockholm, Sweden, with an audience that reflected the 
experimental and interdisciplinary aim of the project, as we discovered that the discussion that the performance could provoke were an inherent, neccecary
and highly satisfying part of such work, and a real meeting-place of professionals of different fields.
Soon after, [Stockholm Stad] awarded us with an [innovation grant](http://www.innovativkultur.se/sv/projektsida/), 
which allowed us some budget to organize private meetings,
public performances as well as start on some [hardware development]. By now, Robert also got more involved we realized that 
programming the EEGsynth in MATLAB was unsustainable. Perhaps the main reason was that by now we realized that to really
bridge the gap between artists and scientists we would have to come up with a way to use the EEGsynth that does not 
neccecitate familiarity with MATLAB and the FieldTrip toolbox. We imagined even a 'plug and play' solution in which we
would install the EEGSynth in a [Raspberry-Pi] (a small cheap mini-computer the size of a pack of cigarettes) that would 
output control signals for modular synthesizers. This would not be possible with a heavy commercial toolbox such as 
MATLAB. In fact, MATLAB just us not a programming platform that is optimal for real-time processing, at least not in the
way that we started to understand our needs. We needed a light way, where many processes would run in parallel and
communicate with each other in a transparant and flexible way. In other words, we realized we needed something like a 
modular synthesizer, packed in a small box, that could be patched flexibly by non-programmers. Furthermore, it needed 
to be real-time in more than one way: not only would the EEG be analyzed and transformed into signals that could control
live equipment, but we wanted an interface with the software that did not necessitate typing lines of code, but rather
the turn of a knob, or the press of a button. And since we were more interested in sound and portability, we did not 
want to rely on a monitor for any of the feedback, so had to find other ways to interact with the code rather than your
typical mouse, keyboard and monitor. In short, during a a two day meeting we reimagined the EEGsynth, 
needing a total rewrite of the code in another language ([Python](https://www.python.org/) on a [Raspberry Pi]. In a way, this was the true 
beginning of the codebase that is now the EEGsynth. Much has happened since, and although the
EEGsynth is not plug-and-play yet, it has in other ways exceeded our expectations. The more clear and modular code 
made it easier to develop in a distributed way using GitHub, as well as presenting more bite-sized structures for distributed 
development such as in hackathons (see e.g. [Paris Hackathon]) and teaching about Brain-Computer-Interfaces (BCIs), 
which we did at the [Centre of Interdisciplinary research]. The technical development 
keps following the requirements and ideas developed through performances and artistic research within 1+1=3. This is the
reason that by now the EEGsynth can interface with performative equipment via e.g. MIDI, CV/gate, DMX, Open Sound 
Controls, ArtNet, etc.  
Importantly, our understanding of the history of experimental music was further enriched when our long-term friend and 
collaborator Samon Takahashi joined us. Were were then even more able to contextualize our work with lectures (e.g. 
during the [Semaine de Cerveau]) or installations on the topic (e.g. at the [Charcot Library]). It became even more clear
what we were doing was another iteration within a fascinating interwoven histories of 
art and science in transducing 'invisible' signals, thereby opening previously closed windows onto reality a nd experience. 
While the EEGsynth allows artists a foray into science and technology, it has also created many opportunities for scientists 
involved to contribute and express themselves artistically. In fact, the distinction between the two has gradually disappeared, 
and have naturally become two sides of the same coin (see e.g. [Hemispherics]). This is a lot of fun for us, and also 
allows us to interface with the full range of audiences and institutions (see e.g. [Technoshamanish], [Brain Brunch], [Bandcamp]).
1+1=3 has not been the only artistic collaboration in which the EEGsynth has been used or inspired its development. 
Since 2016, we have been part of an ambition interdisciplinary project called [COGITO] by the artist Daniela de Paulis. 
In short, the technical aspect
of the project involved the transformation (transduction) of 32-channel EEG into sound in such a way that no information 
is lost. However, no obvious musical aspect is gained, as typically the purpose within 1+1=3. The sound is then transmitted (transduced again) into 
radio waves and transmitted into space using large (25 metre) radio-telescope. While within the other projects we focused 
on creating control signals for sound generation, within [COGITO] we learned about how to directly create sound based on the
EEG, something that will surely feature in future performances. Finally, the EEGsynth is now part of a scientific research project, emphasizing the maturity
of the project. 

To conclude, technically we have explored some of the scope of the EEGsynth and have seen that the architecture of the EEGsynth has 
indeed achieved the desired flexibility, while further development can occur incrementally by means of the development 
of additional modules. Artistically, we find ourselves in the midst of a field with has a short but dense history.
Many paths in biofeedback and neurofeedback have been identified, some explored in art, and some in science, both littered with
hype and broken promises. Many interesting questions can be found laying wayside, dried out and unanswered, while others have are 
bloated and oversold, resulting in inflation of artistic (and scientific) value. Like in any other field, it is a
question of constructing new meaning and new value from this rubble, and using the achievements of the past to image the 
future. The EEGsynth is developed to be a tool for this construction, to be used by interdsciplinary teams such as 1+1=3.

When you start an project with the EEGsynth, one should really consider setting up such as team, nvolving not only an 
artist, but also a (neuro)scientist who understands the material (brains) and instrumentation (EEG) that you will 
be working with. Furthermore, although we try to make it as easy as possible, and in prinicple not requiring programming
experience, we might not be at that point yet. In fact, although we now have the tools, we should now spend our time 
writing the manual. This is what follows now. Please send us any comments and suggestions, either using the [contact form]
or via our [github] repository, where we welcome any suggestions and pull requests. Until then, we wish you all the fun
and discovering that come from exploring this exciting field.

## Design of the EEGsynth

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

![Example of complex modular synthesizer patch](http://www.modcan.com/mainImages/bphoto/bigA.jpg "Example of complex modular synthesizer patch")

**Figure 1.** *Example of complex modular synthesizer patch*

## Patching 


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

## Contributing
It is strongly advised to work within you own cloned repository and keep up to date with EEGsynth commits, as the EEGsynth is in constant development.
* For installation please follow our installation instructions for [Linux](https://github.com/eegsynth/eegsynth/blob/master/doc/installation-linux.md), [OSX](https://github.com/eegsynth/eegsynth/blob/master/doc/installation-osx.md) and [Windows](https://github.com/eegsynth/eegsynth/blob/master/doc/installation-windows.md). Please note that Windows and OSX are not actively supported. Linux is the main target, partly because we want the EEGsynth to be compatible with the [Raspberry Pi](http://raspberrypi.org/), partly because some Python libraries do not support Windows, and partly because we rely on command-line interface anyway.