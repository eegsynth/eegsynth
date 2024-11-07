# README

![logo](doc/figures/EEGsynth_logo.svg?sanitize=true)

The EEGsynth is a [Python](https://www.python.org/) codebase released under the [GNU general public license]( https://en.wikipedia.org/wiki/GNU_General_Public_License) that provides a real-time interface between (open-hardware) devices for electrophysiological recordings (e.g., EEG, EMG and ECG) and analogue and digital devices (e.g., MIDI, lights, games and analogue synthesizers). The EEGsynth allows one to use electrical activity recorded from the brain or body to flexibly control devices in real-time, like (re)active and passive brain-computer-interfaces (BCIs), biofeedback and neurofeedback.

Since December 2018, the EEGsynth is registered as a legal _Association_ with the French authorities.

## Documentation

The EEGsynth code and technical documentation are hosted on [Github](https://github.com/eegsynth) and organized as follows:

* [src/eegsynth](https://github.com/eegsynth/eegsynth/tree/master/src/eegsynth) contains the EEGsynth application (see below)
* [src/module](https://github.com/eegsynth/eegsynth/tree/master/src/module) contains individual modules and reference dopcumentation
* [src/lib](https://github.com/eegsynth/eegsynth/tree/master/src/lib) contains some libraries
* [doc](https://github.com/eegsynth/eegsynth/tree/master/doc) contains the general documentation
* [patches](https://github.com/eegsynth/eegsynth/tree/master/patches) contains patches and documentation of past performances
* [hardware](https://github.com/eegsynth/eegsynth-hardware) contains documentation on some custom hardware

## Installation

You can install the EEGsynth with `pip install eegsynth`. Further installation details can be found in the [documentation](https://github.com/eegsynth/eegsynth/blob/master/doc/installation.md).

## Running the EEGsynth

Following installation of the EEGsynth and starting Redis, you can start `eegsynth *.ini` from a terminal with all ini files contained in a patch, for example like this

```console
eegsynth buffer.ini generatesignal.ini plotsignal.ini
```

or you can start it one module at a time by starting multiple terminals, each with a separate EEGsynth instance, like this

```console
eegsynth buffer.ini
eegsynth generatesignal.ini 
eegsynth plotsignal.ini
```

or you can start the graphical user interface (GUI) like this

```console
eegsynth --gui
```

You can subsequently drag-and-drop the ini files that you want to start into the GUI. After editing an ini file, you can simply drop it into the GUI again and the module will automatically restart; there is no need to stop and restart all of them.

## Disclaimer

The EEGsynth does not allow diagnostic investigations or clinical applications. It also does not provide a graphical user interface for offline analysis. Rather, the EEGsynth is intended as a collaborative interdisciplinary [open-source](https://opensource.com/open-source-way) and [open-hardware](https://opensource.com/resources/what-open-hardware) project that brings together programmers, musicians, artists, neuroscientists and developers in scientific and artistic exploration.

Although there are plans to make it more 'plug-and-play', the EEGsynth currently has to be run from the command line, using [Python](https://www.python.org/) and [Bash](https://en.wikipedia.org/wiki/Bash_%28Unix_shell%29) scripts, and is therefore not friendly for those not familiar with such an approach.

## Collaborate and get more information

When you start an project with the EEGsynth, consider doing it together with in a group of people that have knowledge and experience complimentary to yours, such as in electrophysiology, neuroscience, psychology, programming, computer science or signal processing.

More information can be found at [our website](https://www.eegsynth.org).  Follow us on [Facebook](https://www.facebook.com/EEGsynth/) and [Twitter](https://twitter.com/eegsynth), and check our past and upcoming events on [our calendar](http://www.eegsynth.org/?calendar=eegsynth-calendar). Please feel free to contact us via our [contact form](http://www.eegsynth.org/?page_id=233).
