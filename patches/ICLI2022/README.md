# Patch for the International Conference on Live Interfaces [(ICLI)](https://liveinterfaces.ulusofona.pt/program/), June 21th



This patch was used for ICLI, organized by the Universidade Lusófona de Humanidades e Tecnologias, Lisboa, Portugal

The patch takes EEG data via LSL, in this case provided by the Mentalab Explore EEG, recorded from the brain of Stephen Whitmarsh (Paris). It calculates power of alpha and beta power at manually adjustable frequency ranges, calibrates and scales them, before sending them as OSC messages to localhost.

Locally (Paris), a PureData patch (included) is running on the same desktop Windows computer, which transforms OSC messages into continuous control signals (DC) and sends them to an ES-9 Expert Sleepers module, mounted in a eurorack modular synthesizer. 

At the same time, the PureData patch receives control signals send by Atau Takana (London) over internet, created live by EMG performances using the (out of production) Myo armband and Max/MSP patches. The local  PureData patch then sends these values as continuous DC signals to the ES-9 module.

Simultaneously, audio from the EMG performance in London is streamed with low-latency using JackTrip, to a separate laptop in Paris, using the Zoom H6 as an ASIO audio device. Line-out of the H6 is send to the modular eurorack synthesizer using an Intellijel Audio Interface for raising the signal to modular voltage standards.

In the eurorack modular synthesizer, the sound of the EMG performance by Atau Takaka, as well as oscillators and other sounds sources, are fed through filters and other modulation sources, using the EEG and EMG control signals (i.e. received from the ES-9 DC-coupled audio interface).

The resultant audio from the eurorack modular synthesizer is send to the Zoom conference via an Allen & Heath ZED14 analog audio mixer connected to the main desktop computer, via its digital USB interface, using Zoom's Original Audio setting (stereo and without noise reduction).

OBS is used to compile a visualization of EEG, a video stream of the modular eurorack synthesizer, and the PureData patch, into a preview window, which is shared as a video stream to the conference participants.
