# Robinson

This is the patch used for the first residency at the new EEGsynth HQ in Paris.

See this [link](http://www.eegsynth.org/?p=1580) for details.

We recorded EEG from a single subject on a Linux Mint laptop, controlling a modular synthesizer via the Endorphines Cargo. The subject also used a microphone connected to his MacBook on which Ableton Live was adding a chorus/reverb, then plugged into the mixer together with the modular.

Some technical observations:

- While we sampled all 8 channels, we only used channel number 1 and 8 for plotting and control. This patch is consistent now in this regard, and the signal was great.
- I had some denaturalized alcohol in the house, and this might certainly have improved signal, especially since the subject had used a lot of gel in his hair.
- Discovered and fixed a bug in plotting non-contiguous channels (e.g. 1 and 8 instead of 1 and 2) in `plotsignal`.
- We used the option in the `endorphines` module to add a slide/glide/portamento to the output of the Endorphines Cargo, but as it known, it doesn't easily take the command from the LaunchControl, so quick change of portamento is something to be optimized, or at least set at the onset.
