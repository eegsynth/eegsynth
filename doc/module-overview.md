
# Module overview

Detailed information about each module can be found in the README.md included in each module directory. Here follows a description of the currently available modules. Please note that this list might not be up-to-date, check the code to be sure.

## Analysis

* [Spectral](https://github.com/eegsynth/eegsynth/tree/master/module/spectral) Analyzes power in frequency bands in the raw data buffer
* [Muscle](https://github.com/eegsynth/eegsynth/tree/master/module/muscle) Calculates RMS from EMG recordings in the raw data buffer
* [Accelerometer](https://github.com/eegsynth/eegsynth/tree/master/module/accelerometer) Extracts accelerometer data (X,Y,Z) from onboard sensor of the OpenBCI  in the raw data buffer
* [EyeBlink](https://github.com/eegsynth/eegsynth/tree/master/module/eyeblink) Detects eye blinks in the raw data buffer
* [HeartRate](https://github.com/eegsynth/eegsynth/tree/master/module/heartrate) Extracts heart rate in the raw data buffer

## Data acquisition

* [Openbci2ft](https://github.com/eegsynth/eegsynth/tree/master/module/openbci2ft) Records raw data from the OpenBCI amplifier and places it in the buffer.
* [Bitalino2ft](https://github.com/eegsynth/eegsynth/tree/master/module/bitalino2ft) Records raw data from the Bitalino amplifier and places it in the buffer.
* [Jaga2ft](https://github.com/eegsynth/eegsynth/tree/master/module/jaga2ft) Records raw data from Jaga amplifier and places it in the buffer
* For more supported acquisition devices [look here](http://www.fieldtriptoolbox.org/development/realtime/implementation)

## Communication between modules

* [Redis](https://github.com/eegsynth/eegsynth/tree/master/module/Redis) The database for communicating ccontrol values and messages between modules
* [Buffer](https://github.com/eegsynth/eegsynth/tree/master/module/buffer) FieldTrip buffer for communicating raw data

## Utilities for optimizing data flow, patching and prototyping

* [Recordsignal](https://github.com/eegsynth/eegsynth/tree/master/module/recordsignal) Record raw data to file
* [Playbacksignal](https://github.com/eegsynth/eegsynth/tree/master/module/playbacksignal) Play back pre-recorded raw data
* [Plotsignal](https://github.com/eegsynth/eegsynth/tree/master/module/plotsignal) Plot raw data and power spectra
* [Recordcontrol](https://github.com/eegsynth/eegsynth/tree/master/module/recordcontrol) Record control values from Redis to file
* [Playbackcontrol](https://github.com/eegsynth/eegsynth/tree/master/module/playbackcontrol) Play back pre-recorded control values
* [Plotcontrol](https://github.com/eegsynth/eegsynth/tree/master/module/plotcontrol) Plot control signals from Redis
* [Postprocessing](https://github.com/eegsynth/eegsynth/tree/master/module/postprocessor) Allows computations, algorithms and combinations on the control values
* [Preprocessing](https://github.com/eegsynth/eegsynth/tree/master/module/preprocessor) Filtering and preprocessing of raw data, results get written to another raw data buffer

## External interfaces (open-source)

* [InputMIDI](https://github.com/eegsynth/eegsynth/tree/master/module/inputmidi) Receive MIDI signals
* [OutputMIDI](https://github.com/eegsynth/eegsynth/tree/master/module/outputmidi) Send MIDI signals
* [InputOSC](https://github.com/eegsynth/eegsynth/tree/master/module/inputosc) Receive data from [Open Sound Control](http://opensoundcontrol.org/introduction-osc) protocol
* [OutputOSC](https://github.com/eegsynth/eegsynth/tree/master/module/outputosc) Send data via [Open Sound Control](http://opensoundcontrol.org/introduction-osc) protocol
* [InputAudio](https://github.com/eegsynth/eegsynth/tree/master/module/InputAudio) Receive (sound) from soundcard
* [OutputAudio](https://github.com/eegsynth/eegsynth/tree/master/module/outputaudio) Send (sound) to soundcard
* [OutputArtNet](https://github.com/eegsynth/eegsynth/tree/master/module/outputartnet) Send data according to [Art-Net protocol](https://en.wikipedia.org/wiki/Art-Net)
* [OutputDMX](https://github.com/eegsynth/eegsynth/tree/master/module/outputdmx512) Send data according to [DMX512 protocol](https://en.wikipedia.org/wiki/DMX512)
* [OutputCVgate](https://github.com/eegsynth/eegsynth/tree/master/module/outputcvgate) Send continuous voltages for interfacing with analogue synthesizers using [our own hardware](http://www.ouunpo.com/eegsynth/?page_id=516)

## External interfaces (consumer)

* [LaunchControl](https://github.com/eegsynth/eegsynth/tree/master/module/launchcontrol) Records and send data to the Novation [LaunchControl](https://global.novationmusic.com/launch/launch-control) and [LaunchControl XL](https://global.novationmusic.com/launch/launch-control-xl) MIDI controllers
* [LaunchPad](https://github.com/eegsynth/eegsynth/tree/master/module/launchpad) Record and send data to the Novation [Launchpad](https://global.novationmusic.com/launch/launchpad) MIDI controller
* [VolcaBass](https://github.com/eegsynth/eegsynth/tree/master/module/volcabass) Interface with the Korg [Volca Bass](http://www.korg.com/us/products/dj/volca_bass/) synthesizer
* [VolcaBeats](https://github.com/eegsynth/eegsynth/tree/master/module/volcabeats) Interface with the Korg [Volca Beats](http://www.korg.com/us/products/dj/volca_beats/) synthesizer
* [VolcaKeys](https://github.com/eegsynth/eegsynth/tree/master/module/volcakeys) Interface with the Korg [Volca Keys](http://www.korg.com/us/products/dj/volca_keys/) synthesizer
* [Endorphines](https://github.com/eegsynth/eegsynth/tree/master/module/endorphines) Interface with Endorphines’ [Shuttle Control](https://endorphin.es/endorphin.es--modules.html) MIDI to CV module
* [Keyboard](https://github.com/eegsynth/eegsynth/tree/master/module/keyboard) Records MIDI keyboard note and velocity input

## Software synthesizer modules

* [Generateclock](https://github.com/eegsynth/eegsynth/tree/master/module/generateclock) Generate clock signals, i.e. for gates or for MIDI
* [Sequencer](https://github.com/eegsynth/eegsynth/tree/master/module/sequencer) A basis sequencer to send out sequences of notes
* [Synthesizer](https://github.com/eegsynth/eegsynth/tree/master/module/synthesizer) A basic synthesizer to send our waveforms
* [Quantizer](https://github.com/eegsynth/eegsynth/tree/master/module/quantizer) Quantize output chromatically or according to musical scales

## COGITO project

* [Cogito](https://github.com/eegsynth/eegsynth/tree/master/module/cogito) Streaming EEG data (from the Gtec EEG) to audio for interstellar EEG transmission, as part of the [COGITO](http://www.cogitoinspace.org/) project
