# Module overview

Detailed information about each module can be found in the README.md included in each module directory. Here follows a description of the currently available modules. Please note that this list might not be up-to-date, check the code to be sure.

## Analysis

- [Spectral](../src/module/spectral) Analyzes power in frequency bands in the raw data buffer
- [Muscle](../src/module/muscle) Calculates RMS from EMG recordings in the raw data buffer
- [Accelerometer](../src/module/accelerometer) Extracts accelerometer data (X,Y,Z) from the onboard sensor of the OpenBCI stream in the raw data buffer
- [Threshold](../src/module/threshold) Detects event such a eye blinks in the raw data buffer
- [HeartRate](../src/module/heartrate) Extracts heart rate in the raw data buffer

## Data acquisition

- [Audio2ft](../src/module/audio2ft) Records raw data from the computer's audio input and places it in the buffer
- [Lsl2ft](../src/module/lsl2ft) Records raw data from Lab Streaming Layer and places it in the buffer
- [Unicorn2ft](../src/module/unicorn2ft) Records raw data from the Unicorn amplifier and places it in the buffer
- [Openbci2ft](openbci.md) Records raw data from the OpenBCI amplifier and places it in the buffer
- [Bitalino2ft](../src/module/bitalino2ft) Records raw data from the Bitalino amplifier and places it in the buffer


For more supported acquisition devices [look here](http://www.fieldtriptoolbox.org/development/realtime/implementation)

## Communication between modules

- [Redis](../src/module/Redis) The database for communicating ccontrol values and messages between modules
- [Buffer](../src/module/buffer) FieldTrip buffer for communicating raw data

## Utilities for optimizing data flow, patching and prototyping

- [Recordsignal](../src/module/recordsignal) Record raw data to file
- [Playbacksignal](../src/module/playbacksignal) Play back pre-recorded raw data
- [Plotsignal](../src/module/plotsignal) Plot raw data
- [Plotspectral](../src/module/plotspectral) Plot spectrum of raw data
- [Recordcontrol](../src/module/recordcontrol) Record control values from Redis to file
- [Playbackcontrol](../src/module/playbackcontrol) Play back pre-recorded control values
- [Plotcontrol](../src/module/plotcontrol) Plot control signals from Redis
- [Postprocessing](../src/module/postprocessing) Allows computations, algorithms and combinations on the control values
- [Preprocessing](../src/module/preprocessing) Filtering and preprocessing of raw data, results get written to another raw data buffer
- [Plottrigger](../src/module/plottrigger) Plot pub/sub events from Redis
- [Processtrigger](../src/module/processtrigger) Allows computations, algorithms and combinations on the pub/sub events

# Modules that relate to timing and regular sequences

- [Sequencer](../src/module/sequencer) Play a monophonic sequence as pub/sub events
- [Generatetrigger](../src/module/generatetrigger) Generate pub/sub events at regular intervals
- [Clockdivider](../src/module/clockdivider) Pass every N-th trigger of a regular stream of pub/sub events
- [Clockmultiplier](../src/module/clockmultiplier) Generate N triggers for each trigger in a regular stream of pub/sub events
- [Delaytrigger](../src/module/delaytrigger) Following a pub/sub event, generate a new trigger after a given delay.

## External interfaces (generic software)

- [InputMIDI](../src/module/inputmidi) Receive MIDI signals
- [OutputMIDI](../src/module/outputmidi) Send MIDI signals
- [InputOSC](../src/module/inputosc) Receive data from [Open Sound Control](http://opensoundcontrol.org/introduction-osc) protocol
- [OutputOSC](../src/module/outputosc) Send data via [Open Sound Control](http://opensoundcontrol.org/introduction-osc) protocol
- [InputAudio](../src/module/InputAudio) Receive (sound) from soundcard
- [OutputAudio](../src/module/outputaudio) Send (sound) to soundcard
- [OutputArtNet](../src/module/outputartnet) Send data according to [Art-Net protocol](https://en.wikipedia.org/wiki/Art-Net)

## External interfaces (consumer hardware)

- [LaunchControl](../src/module/launchcontrol) Records and send data to the Novation [LaunchControl](https://global.novationmusic.com/launch/launch-control) and [LaunchControl XL](https://global.novationmusic.com/launch/launch-control-xl) MIDI controllers
- [LaunchPad](../src/module/launchpad) Record and send data to the Novation [Launchpad](https://global.novationmusic.com/launch/launchpad) MIDI controller
- [VolcaBass](../src/module/volcabass) Interface with the Korg [Volca Bass](http://www.korg.com/us/products/dj/volca_bass/) synthesizer
- [VolcaBeats](../src/module/volcabeats) Interface with the Korg [Volca Beats](http://www.korg.com/us/products/dj/volca_beats/) synthesizer
- [VolcaKeys](../src/module/volcakeys) Interface with the Korg [Volca Keys](http://www.korg.com/us/products/dj/volca_keys/) synthesizer
- [Endorphines](../src/module/endorphines) Interface with Endorphines’ [Shuttle Control](https://endorphin.es/endorphin.es--modules.html) MIDI to CV module
- [Keyboard](../src/module/keyboard) Records MIDI keyboard note and velocity input
- [OutputDMX](../src/module/outputdmx) Send data according to [DMX512 protocol](https://en.wikipedia.org/wiki/DMX512)

## External interfaces (DIY hardware)

- [OutputCVgate](../src/module/outputcvgate) Send continuous voltages for interfacing with analogue synthesizers using [our own hardware](https://github.com/eegsynth/eegsynth-hardware)
- [OutputGPIO](../src/module/outputgpio) Send triggers and PWM signals using the Raspberry Pi GPIO pins

## Software synthesizer modules

- [Generateclock](../src/module/generateclock) Generate clock signals, i.e. for gates or for MIDI
- [Sequencer](../src/module/sequencer) A basis sequencer to send out sequences of notes
- [Synthesizer](../src/module/synthesizer) A basic synthesizer to send our waveforms
- [Quantizer](../src/module/quantizer) Quantize output chromatically or according to musical scales

## Cogito project

- [Cogito](../src/module/cogito) Streaming EEG data from the Gtec EEG system to audio for interstellar transmission, as part of the [Cogito](http://www.cogitoinspace.org/) project
