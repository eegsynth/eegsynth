# Manual control

Although the purpose of the EEGsynth (and BCIs in general) is to control devices using 
biological signals, some manual interaction might be desired, e.g. to adjust the dynamics of the 
output or to select the frequency range of the brainsignal during the recording. 
However, as with analogue synthesizers, we like the tactile real-time aspect of knobs and buttons, 
while avoiding using a computer keyboard. We therefor mainly use [MIDI](midi.md) controllers, 
such as the [LaunchControl XL](https://global.novationmusic.com/launch/launch-control-xl#) 
displayed below. Identical to all other modules, the launchcontrol *module* records the 
launchcontrol input from its sliders, knobs, and buttons into the Redis database to be used by other 
modules.

![](https://novationmusic.com/sites/novation/files/LCXL-HeaderImage-2560-1000.png)

*The Novation LaunchControl XL, often used in EEGsynth setups*

_Continue reading: [Visualisation](visualisation.md)_
