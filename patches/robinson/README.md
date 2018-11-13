This is the patch used for the first residency at the new EEGsynth HQ in Paris.

See this [link](http://www.eegsynth.org/?p=1580) for details.

We recorded EEG from a single subject on a Linux Mint laptop, controlling a modular synthesizer via the Endorphines Cargo. The subject also used a microphone connected to his MacBook on which Ableton Live was adding a chorus/reverb, then plugged into the mixer together with the modular.

Some technical observations:
* While we sample all 8 channels, only use channel number 1 and 8 for plotting and control. This patch is consistent now in this regard, and the signal was great.
* I had some denaturalized alcohol in the house, and this might certainly have improved signal, especially since subject used a lot of gel.
* Discovered and fixed a bug in plotting noncontiguous channels (e.g. 1 and 8 instead of 1 and 2) in plotsignal.
* We used the option in the endophines module to add a slide/glide/portamento to the output of the Endorphines Cargo, but as it known, it doesn't easily take the command from the Launchcontrol, so quick change of portamento is something to be optimized, or at least set at the onset.
