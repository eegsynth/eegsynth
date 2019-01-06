# MIDI

For the EEGsynth we are developing and testing with a variety of hardware, some of them using a
MIDI interface. Furthermore, we make use of a variety of software that can be interfaced using MIDI.

## Introduction

MIDI, short for Musical Instrument Digital Interface, is a standard for communication with and between electronic,
or rather digital, musical instruments. Its been around since the early eighties, and is one of those rare examples
where competing companies decided to maintain a common communication protocol allowing their machines to be easily
connected, rather than creating their own protocols, cables, plugs and formats, which is frustratingly common.
MIDI carries event messages that specify notation, pitch, velocity, vibrato, panning, and clock signals which set
tempo. It is therefor close to an ideal protocol for the output of the EEGsynth, since any
pitch, velocity, vibrato and panning are all great sonic parameters to put under BCI control.

MIDI is also very useful to tweak parameters of the EEGsynth, such as frequency bands used in the EEG spectral
analysis or to adjust thresholds on the fly. For example, we often use knobs and sliders
of a MIDI control device (e.g. the Novation [Launch Control XL](https://novationmusic.com/launch/launch-control-xl))
in our live performance, or use it to simulate data in prototyping.

## MIDI as input

Whenever you change the position of knobs or sliders of a MIDI control device,
a MIDI *control* message is sent; in the EEGsynth we map these onto Redis channels which
can be continuously adjusted by one module and used by another.

Another important feature of MIDI are the *note* messages, which are sent whenever you press or
release a button on the Launchcontrol or a key on a keyboard. MIDI note messages have two
values attached to them: one that specifies which key or button was pressed, and the other
that specifies the velocity. For the Launch Control the velocity is 127 when a button is pressed
down, and 0 when released. On a touch sensitive keyboard the note velocity will scale with the
force with which you hit the key; when releasing the key the velocity is specified as zero.

An important characteristic of MIDI notes is that they also convey information about the precise
time of events. To ensure that the timing of MIDI events can be used in the EEGsynth, we
*publish* notes to a Redis channel as messages on. Other modules can subscribe to a channel
and will be notified for each published message. The publish/subscribe mechanism makes it
possible to treat MIDI notes as triggers.

## MIDI clock signal

As we said above, MIDI can also be used to set the speed of a musical device, such as a sequencer.
To understand on how to use MIDI signals to control the speed, we need to understand the terms used in music, and MIDI in particular.

### Tempo
Tempo is the speed at which something is played – e.g. fast and constant in electronic dance music,
and slower and more variable in instrumental music. While between humans a drummer might snap his drumsticks to set
the tempo, and while Latin (e.g. Adagio) and German words (e.g. kräftig) are using in classical music notation,
in digital music we simply use beats per minute (BMP).

### Beats
But what is a beat? Psychologically it’s that moment at which you tap your feet while you are listening to
(or playing) music. And of course in common parlance ‘a beat’ often refers to the sound(s) used for the rhythm.
However, in music theory, beats are the basic units of time that describe the moment when things happen, whether
these are beats on a drum, the stroke of a violin, or a note on a keyboard. In fact, in music theory those events
are described by ‘notes’. How beats are organized in time, and how they relate to notes is where the music starts
to happen.

### Time signature
In music theory, beats are organized in blocks of beats called measures or bars, which then repeat themselves
throughout (parts of) a song. Within a measure, the way in which beats relate to events (notes) is called its
time-signature. The most common time-signature is 4/4, therefor also called ‘common time’. In common time, one bar
consists of four beats, and each beat corresponds to the duration of a quarter-note (one forth of a note).
Wikipedia has a nice page with examples of different time-signatures, if you are interested. For now it’s just good
to know that the elementary sequence of beats is a measure, consisting of a number of beats (commonly 4), which
correspond to a particular note-duration (typically a quarter note).

### Pulses Per Quarter Note
The time-signature says nothing about how slow or fast the notes are played. As I said earlier, that is determined
by its tempo, described in BPM or more subjective descriptions (Andante, i.e. ‘at a walking pace’, referring to
76–108 BPM). The last thing we need to say is a bit technical: for a MIDI instruments to communicate the tempo,
they need more than just one signal for every beat (or quarter-note) to code for slight variations in tempo.
In MIDI, tempo is therefor defined in a number of Pulses Per Quarter Note (PPQN). In most step-sequencers, we are
dealing with a 4/4 time signature with the common default set at 24PPQN, meaning that there are 24 pulses
(or ‘ticks’) in a beat (or quarter-note). A single bar/measure will therefor have a total of 4×24=96 pulses.
Most MIDI devices can be set at another PPQN rate, but 24 PPQN will suffice for most intends and purposes,
especially when dealing with rather dumb step-sequencers.

## MIDI hardware interfacing

The MIDI interfaces may show up differently, depending on the computer to which you connect the
MIDI device, and depending on the software used on that computer.

The software interface to MIDI devices is often implemented over multiple layers.
E.g. on macOS the EEGsynth modules connect with the hardware like this:

EEGsynth (Python) &rarr; **mido** &rarr; **portmidi** &rarr; **coremidi** &rarr; MIDI hardware

## Modules that directly interface with MIDI

* [generateclock](../module/generateclock)
* [sequencer](../module/sequencer)
* [inputmidi](../module/inputmidi)
* [ouputmidi](../module/ouputmidi)
* [launchcontrol](../module/launchcontrol)
* [volcabass](../module/volcabass)
* [volcabeats](../module/volcabeats)
* [volcakeys](../module/volcakeys)

## MIDI hardware we work with (macOS and Linux) for input, output or both

* Novation Launch Control, Launch Control XL and Launchpad
* Korg Volca Beats, Bass and Keys
* Yamaha P-95 digital piano
* Roland V-Drum kit with [TD-9](https://www.roland.com/us/products/td-9/) sound module
* Arturio Microbrute
* Endorphines Shuttle Control
* Generic USB-MIDI converter cables from Ebay

## Software and programming interfaces

* [RtMidi](https://www.music.mcgill.ca/~gary/rtmidi/) is a C++ programming library that is
supported on Linux, macOS and Windows.
* [PortMidi](http://portmedia.sourceforge.net/portmidi/) is a C++ programming library that is supported on Linux, macOS
and Windows.
* [Core MIDI](https://developer.apple.com/library/ios/documentation/MusicAudio/Reference/CACoreMIDIRef/)
is a programming library for macOS.
* [Python/MIDO](https://mido.readthedocs.org) is a Python package that can use either the PortMidi
interface or the RtMidi interface.
* [Python-RtMidi](https://pypi.python.org/pypi/python-rtmidi) is a Python package for RtMidi.
* [RtMidi-Python](https://pypi.python.org/pypi/rtmidi-python) is another Python wrapper for RtMidi.
* [MidiOSC](https://github.com/jstutters/MidiOSC) is a small program to bridge the worlds of MIDI and OSC by providing
bidirectional conversion of MIDI to OSC. It is available for macOS and for Linux. We explain how we
use it [here](midiosc.md).  

## Further reading

[Here](http://tedfelix.com/linux/linux-midi.html) you find a great page with details on Linux command line tools to
explore soundcard and MIDI devices.
