# When the Shimmer of Eternity Starts to Fade

On November 4, 6 and 8 (2025) we welcome you in Stockholm to join an artistic event and a guided tour that explores the timeless rooms of the Hallwyl Museum through new perspectives. The central motif of the evening is mother-of-pearl, which has been used to make jewellery, sacred artefacts, and ceremonial objects across civilisations. With its iridescent beauty the material has not merely been used in decoration; it also symbolises purity, protection, and permanence.

The guided tour brings together dance, visual art, music and science in shimmering darkness, where the rooms, objects and paintings take on new life. Based on the interdisciplinary group’s interest in science and art, they address the fleetingness of life and our dreams of becoming immortal.

See the website of the [Hallwylska Museet](https://hallwylskamuseet.se/en/pa-gang/kalender/) when-the-shimmer-of-eternity-starts-to-fade-english/) or [Vision Forum](https://www.visionforum.eu/h/) for more details.

## Overall setup

![flowchart](patch.png)

We are using a Euromex BioBlue.lab microscope with a CMEX 5.0 MP USB camera to observe the microbes. The live video stream is processed using the EEGsynth and changes in the video (due to the microbes moving around) are sent over OSC as control signals to TouchDesigner (running on another laptop) and Ableton Live (running on yet another computer).

The live video stream from the microscope is also shared as-is with TouchDesigner on the other computer for creating visuals and video-mixing. To share the video, we are using NDI Scan Converter to capture the videoprocessing window. The NDI stream is subsequently displayed on a second "virtual" screen using NDI Video Monitor. The second screen is actually a Macrosilicon HDMI-to-USB capture card plugged into the computer running TouchDesigner. On the TouchDesigner computer we capture the live video stream as if it were a webcam and crop it a bit to remove the menu bar and the window borders.

## EEGsynth screenshot

The screenshot below shows the EEGsynth graphical user interface with the videoprocessing, inputcontrol, vumeter, and plotcontrol modules. Not visible are the historycontrol, postprocessing, and outputosc modules.

![screenshot](screenshot.png)
