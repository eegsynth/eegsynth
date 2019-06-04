# Modular design

The design of the EEGsynth is modular, directly inspired by [modular synthesizers](https://en.wikipedia.org/wiki/Modular_synthesizer), such as the Doepfer A-100 below:

![](https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/Doepfer_A-100.jpg/330px-Doepfer_A-100.jpg)

Every module does a specific task. Each module consists of a single Python script, and is contained in its own directory.

For instance, in the directory [module/launchcontrol](https://github.com/eegsynth/eegsynth/module/launchcontrol) we find:

- [launchcontrol.py](https://github.com/eegsynth/eegsynth/module/launchcontrol/launchcontrol.py) which is the [Python](https://www.python.org/) script. Read more about the Python scripts [here](scripts.md).
- [launchcontrol.ini](https://github.com/eegsynth/eegsynth/module/launchcontrol/launchcontrol.ini) which is the initialization file setting the parameters and the way it's connected. Read more about the ini files [here](inifile.md)
- [README.md](https://github.com/eegsynth/eegsynth/module/launchcontrol/README.md) which is the explanation of the module in [markdown](https://en.wikipedia.org/wiki/Markdown) format

As in modular synthesizers, the EEGsynth works by having several modules interconnected, sending and receiving information between each other. Similarly as in modular synthesizers, we call this _patching_. Read more about how we implement patching [here](patching.md), or go [here](module-overview.md) for the module overview.

_Continue reading: [Python scripts](scripts.md)_
