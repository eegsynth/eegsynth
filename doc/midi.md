# MIDI

For the EEGsynth we are developing and testing with a variety of hardware, some of them using a MIDI interface. Furthermore, we make use of a variety of software that can be interfaced using MIDI.

MIDI is useful for a number of features of the EEGsynth. For example, the knobs and sliders on the Novation [Launch Control XL](https://novationmusic.com/launch/launch-control-xl) are very useful to tweak the parameters of the EEGsynth, such as frequency bands used in the EEG spectral analysis or to adjust thresholds on the fly. Whenever you change the position of these knobs and sliders, a MIDI *control* message is sent; in the EEGsynth we map these onto Redis channels which can be continuously adjusted by one module and used by another.

Another important feature of MIDI are the *note* messages, which are sent whenever you press or release a button on the Launchcontrol or a key on a keyboard. MIDI note messages have two values attached to them: one that specifies which key or button was pressed, and the other that specifies the velocity. For the Launch Control the velocity is 127 when a button is pressed down, and 0 when released. On a touch sensitive keyboard the note velocity will scale with the force with which you hit the key; when releasing the key the velocity is specified as zero.

An important characteristic of MIDI notes is that they also convey information about the precise time of events. To ensure that the timing of MIDI events can be used in the EEGsynth, we *publish* notes to a Redis channel as messages on. Other modules can subscribe to a channel and will be notified for each published message. The publish/subscribe mechanism makes it possible to treat MIDI notes as triggers.


## Hardware

- Novation Launch Control, Launch Control XL and Launchpad
- Korg Volca Beats, Bass and Keys
- Yamaha P-95 digital piano
- Roland V-Drum kit with [TD-9](https://www.roland.com/us/products/td-9/) sound module
- Arturio Microbrute
- Endorphines Shuttle Control
- USB-MIDI converter cable from Ebay


## Software and programming interfaces

The MIDI interfaces may show up differently, depending on the computer to which you connect the MIDI device, and depending on the software used on that computer.

The software interface to MIDI devices is often implemented over multiple layers. E.g. on OS X the EEGsynth modules connect with the hardware like this:

eegsynth->python->mido->portmidi->coremidi->hardware

### RtMidi

This is a C++ programming library that is supported on Linux, OS X and Windows.
See https://www.music.mcgill.ca/~gary/rtmidi/

### PortMidi

This is a C++ programming library that is supported on Linux, OS X and Windows.
See http://portmedia.sourceforge.net/portmidi/

### Core MIDI

This is a programming library for OS X.
See https://developer.apple.com/library/ios/documentation/MusicAudio/Reference/CACoreMIDIRef/

### Python/MIDO

This is a Python package that can use either the PortMidi interface or the RtMidi interface.
See https://mido.readthedocs.org

### Python-RtMidi

This is a Python package for RtMidi.
See https://pypi.python.org/pypi/python-rtmidi

### RtMidi-Python

Another Python wrapper for RtMidi. For Linux, Mac OS X and Windows. This uses the same API as RtMidi, only reformatted to comply with PEP-8, and with small changes to make it a little more pythonic.
See https://pypi.python.org/pypi/rtmidi-python

### MidiOSC

This is an open source C++ application that uses the RtMidi interface.
See https://github.com/jstutters/MidiOSC

### TouchOSC Bridge

This is a closed source application for OS X or Windows.
See http://hexler.net/docs/touchosc-getting-started-midi

### OSCulator

This is a closed source application for OS X.
See http://www.osculator.net

### AVMixer

This is a closed source application for OS X only.
See https://neuromixer.com/products/avmixer-pro

## Further reading

On http://tedfelix.com/linux/linux-midi.html you can find a great page with details on Linux command line tools to explore soundcard and MIDI devices.
