# Baseline module

The purpose of this module is to compute a baseline correction using a fixed baseline that is recorded at the launch of the script.
This is different from correcting the signal using historycontrol + postprocessing because it normalizes incoming values by a
fixed distribution (instead of a moving one), in order to observe relative changes with a baseline state. 
