# MIDI

For the EEGsynth we are developing and testing with a variety of hardware, some of them using a MIDI interface. Furthermore, we make use of a variety of software.

## Hardware

- Novation Launch Control, Launch Control XL and Launchpad
- Korg Volca Beats, Bass and Keys
- Yamaha P-95 digital piano (keyboard)
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
