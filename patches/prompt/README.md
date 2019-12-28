# PROMPT - Personalized care and Research On Motoric dysfunctioning for Patient-specific Treatments

This patch synchronizes the experimental setup for the PROMPT project. Participants are walking in a hallway, while fNIRS, Xsens motion capture and video (3x) are recorded. The synchronization of the Artinis fNIRS equipment is only possible through LSL, hence we also use LSL to synchronize the Xsens (though GPIO TTLs) and the video (through audio beeps).

The patch includes
- `inputlsl` module that receives the LSL start, stop and sync messages
- `sampler` module to play the audio beeps
- `outputgpio` module for the TTL triggers

The start, stop and sync LSL messages are generated from an experimental control PC running MATLAB, Psychtoolbox and liblsl-Matlab.

The patch is installed on 4 Raspberry Pi's that are connected over the WiFi network: one is connected to the Xsens receiver, three are connected to the video camera's. The NIRS system receives the LSL messages over the WiFi network. Each Raspberry Pi is running a independent EEGsynth installation, receiving (and responding to) the same LSL messages.

## Implementation notes

The built-in audio of the Raspberry Pi 3B has a default sample rate of 48000 Hz.

To start it automatically, you can create the files

- `$HOME/.config/systemd/user/eegsynth-inputlsl.service`
- `$HOME/.config/systemd/user/eegsynth-sampler.service`
- `$HOME/.config/systemd/user/eegsynth-outputgpio.service`

Each of these should contain something like this

```
[Unit]
Description=EEGsynth inputlsl module
After=redis-server.service

[Service]
ExecStart=%h/eegsynth/patches/prompt/raspberry/inputlsl.sh
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
```

To have the services started automatically, you would do

    systemctl --user enable eegsynth-inputlsl
    systemctl --user enable eegsynth-sampler
    systemctl --user enable eegsynth-outputgpio

To start the service even when the user is not logged in, you would do

    sudo loginctl enable-linger <username>

The use of systemd for user services is explained [here](https://www.shellhacks.com/systemd-service-file-example/) and [here](https://wiki.archlinux.org/index.php/Systemd/User).
