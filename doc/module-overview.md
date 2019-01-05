
# Module overview

Detailed information about each module can be found in the README.md included in each module directory. Here follows a description of the currently available modules. Please note that this list might not be up-to-date, check the code to be sure.

## Analysis

* [Spectral](../module/spectral) Analyzes power in frequency bands in the raw data buffer
* [Muscle](../module/muscle) Calculates RMS from EMG recordings in the raw data buffer
* [Accelerometer](../module/accelerometer) Extracts accelerometer data (X,Y,Z) from onboard sensor of the OpenBCI  in the raw data buffer
* [EyeBlink](../module/eyeblink) Detects eye blinks in the raw data buffer
* [HeartRate](../module/heartrate) Extracts heart rate in the raw data buffer

## Data acquisition

* [Openbci2ft](../module/openbci2ft) Records raw data from the OpenBCI amplifier and places it in the buffer.
* [Bitalino2ft](../module/bitalino2ft) Records raw data from the Bitalino amplifier and places it in the buffer.
* [Jaga2ft](../module/jaga2ft) Records raw data from Jaga amplifier and places it in the buffer
* For more supported acquisition devices [look here](http://www.fieldtriptoolbox.org/development/realtime/implementation)

## Communication between modules

* [Redis](../module/Redis) The database for communicating ccontrol values and messages between modules
* [Buffer](../module/buffer) FieldTrip buffer for communicating raw data

## Utilities for optimizing data flow, patching and prototyping

* [Recordsignal](../module/recordsignal) Record raw data to file
* [Playbacksignal](../module/playbacksignal) Play back pre-recorded raw data
* [Plotsignal](../module/plotsignal) Plot raw data
* [Plotspectral](../module/plotspectral) Plot spectrum of raw data
* [Recordcontrol](../module/recordcontrol) Record control values from Redis to file
* [Playbackcontrol](../module/playbackcontrol) Play back pre-recorded control values
* [Plotcontrol](../module/plotcontrol) Plot control signals from Redis
* [Postprocessing](../module/postprocessing) Allows computations, algorithms and combinations on the control values
* [Preprocessing](../module/preprocessing) Filtering and preprocessing of raw data, results get written to another raw data buffer
* [Plottrigger](../module/plottrigger) Plot pub/sub events from Redis

## External interfaces (open-source)

* [InputMIDI](../module/inputmidi) Receive MIDI signals
* [OutputMIDI](../module/outputmidi) Send MIDI signals
* [InputOSC](../module/inputosc) Receive data from [Open Sound Control](http://opensoundcontrol.org/introduction-osc) protocol
* [OutputOSC](../module/outputosc) Send data via [Open Sound Control](http://opensoundcontrol.org/introduction-osc) protocol
* [InputAudio](../module/InputAudio) Receive (sound) from soundcard
* [OutputAudio](../module/outputaudio) Send (sound) to soundcard
* [OutputArtNet](../module/outputartnet) Send data according to [Art-Net protocol](https://en.wikipedia.org/wiki/Art-Net)
* [OutputDMX](../module/outputdmx512) Send data according to [DMX512 protocol](https://en.wikipedia.org/wiki/DMX512)
* [OutputCVgate](../master/module/outputcvgate) Send continuous voltages for interfacing with analogue synthesizers using [our own hardware](http://www.ouunpo.com/eegsynth/?page_id=516)

## External interfaces (consumer)

* [LaunchControl](../module/launchcontrol) Records and send data to the Novation [LaunchControl](https://global.novationmusic.com/launch/launch-control) and [LaunchControl XL](https://global.novationmusic.com/launch/launch-control-xl) MIDI controllers
* [LaunchPad](../module/launchpad) Record and send data to the Novation [Launchpad](https://global.novationmusic.com/launch/launchpad) MIDI controller
* [VolcaBass](../module/volcabass) Interface with the Korg [Volca Bass](http://www.korg.com/us/products/dj/volca_bass/) synthesizer
* [VolcaBeats](../module/volcabeats) Interface with the Korg [Volca Beats](http://www.korg.com/us/products/dj/volca_beats/) synthesizer
* [VolcaKeys](../module/volcakeys) Interface with the Korg [Volca Keys](http://www.korg.com/us/products/dj/volca_keys/) synthesizer
* [Endorphines](../module/endorphines) Interface with Endorphines’ [Shuttle Control](https://endorphin.es/endorphin.es--modules.html) MIDI to CV module
* [Keyboard](../module/keyboard) Records MIDI keyboard note and velocity input

## Software synthesizer modules

* [Generateclock](../module/generateclock) Generate clock signals, i.e. for gates or for MIDI
* [Sequencer](../module/sequencer) A basis sequencer to send out sequences of notes
* [Synthesizer](../module/synthesizer) A basic synthesizer to send our waveforms
* [Quantizer](../module/quantizer) Quantize output chromatically or according to musical scales

## COGITO project

* [Cogito](../master/module/cogito) Streaming EEG data (from the Gtec EEG) to audio for interstellar EEG transmission, as part of the [COGITO](http://www.cogitoinspace.org/) project
