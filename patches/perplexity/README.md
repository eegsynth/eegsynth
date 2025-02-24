# Perplexity 2024 - Sonifications: a one-day festival on Microbes in Art and Science

University Ghent, Belgium - 18 June 2024

Discover the sounds of genetically modified microorganisms singing - encounter bacteria that generate their own films and soundtracks in real time - hear and see single bacteria playing graphene drums?

In the second edition of the annual Perplexity event, musicians, artists, researchers, and thinkers come together for a day of reflection on microbes and sound. During Perplexities, we invite you to be curious, less serious, and more speculative!

## Overall setup

![flowchart](patch.png)

We are using a Euromex BioBlue.lab microscope with a CMEX 5.0 MP USB camera to observe the microbes. The live video stream is processed using the EEGsynth and changes in the video (due to the microbes moving around) are sent over OSC as control signals to TouchDesigner (running on another laptop) and Ableton Live (running on yet another computer).

The live video stream from the microscope is also shared with TouchDesigner through an HDMI splitter and a HDMI-to-USB capture card. TouchDesigner is used for video-mixing and creating visuals.

## EEGsynth screenshot

The screenshot below shows the EEGsynth graphical user interface with the videoprocessing, inputcontrol, vumeter, and plotcontrol modules. Not visible are the historycontrol, postprocessing, and outputosc modules.

![screenshot](screenshot.png)
