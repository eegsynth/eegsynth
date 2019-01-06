# Using MidiOSC

[MidiOSC](https://github.com/jstutters/MidiOSC) is a small program to bridge the worlds of MIDI and OSC by providing bidirectional conversion of MIDI to OSC. It is available for macOS and for Linux.

Compared to [TouchOSC Bridge](http://hexler.net/docs/touchosc-getting-started-midi) it has the advantage that any MIDI messages can be transferred over the network, not only those from the TouchOSC application running on your tablet or smartphone.

Compared to [OSCulator](http://www.osculator.net) it has the advantage that it is free (although OSCulator is not that expensive). Furthermore, for EEGsynth it would not be so convenient to configure the mapping/translation between OSC and MIDI commands in the OSCulator application. For other situations where you don't control the OSC-sending software, this configurability would actually be an advantage.

## Getting MidoOSC running on Raspbian

```
sudo apt-get install scons
sudo apt-get install liblo-dev
sudo apt-get install libasound2-dev

git clone https://github.com/jstutters/MidiOSC.git
cd MidiOSC
scons
```

The previous resulted in a working application, but it would not find any of the connected MIDI devices.

```
sudo apt-get install jackd2
```


## Getting MidoOSC running on macOS

I am using [macports](https://www.macports.org) as package manager on macOS.

```
sudo port install liblo
sudo pip install --global-option=build_ext --global-option="-I/opt/local/include/" --global-option="-L/opt/local/lib/" pyliblo

sudo port install scons

git clone https://github.com/jstutters/MidiOSC.git
cd MidiOSC
scons
```

The *pyliblo* Pthon package is only needed for testing the example.py  script provided in MidiOSC.

I had to make the following changes to the SConstruct file to deal with the liblo header and library being in /opt/local, which is the default place for macports.

```
diff --git a/SConstruct b/SConstruct
index 9bb9c7f..2dde119 100644
--- a/SConstruct
+++ b/SConstruct
@@ -5,7 +5,7 @@ libs = ['lo']
 if sys.platform == 'darwin':
     env = Environment(
         FRAMEWORKS = ['CoreMidi', 'CoreAudio', 'CoreFoundation'],
-        CCFLAGS = '-D__MACOSX_CORE__'
+        CCFLAGS = '-D__MACOSX_CORE__ -I/opt/local/include'
     )
 else:
     env = Environment(
@@ -13,4 +13,4 @@ else:
     )
     libs.append(['asound', 'pthread'])

-env.Program('midiosc', ['main.cpp', 'midiinput.cpp', 'RtMidi.cpp', 'anyoption.cpp', 'options.cpp'], LIBS=libs)
+env.Program('midiosc', ['main.cpp', 'midiinput.cpp', 'RtMidi.cpp', 'anyoption.cpp', 'options.cpp'], LIBS=libs, LIBPATH='/opt/local/lib')
```

## Translating messages

The EEGsynth.midiwrapper class translates [mido](https://mido.readthedocs.org/en/latest/) messages automatically to OSC messages. The OSC messages are formatted such that the MidiOSC application will convert them back to the appropriate MIDI message on the receiving computer.
