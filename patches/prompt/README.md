# PROMPT - Personalized care and Research On Motoric dysfunctioning for Patient-specific Treatments

This patch synchronizes the experimental setup for the PROMPT project. Participants are walking in a hallway, while fNIRS, Xsens motion capture and video (3x) are recorded. The synchronization of the Artinis fNIRS equipment is only possible through LSL, hence we also use LSL to synchronize the Xsens (though GPIO TTLs) and the video (through audio beeps).

The patch includes
- `inputlsl` module that receives the LSL start, stop and sync messages
- `outputgpio` module for the TTL triggers
- `sampler` module to play the audio beeps

The start, stop and sync LSL messages are generated from an experimental control PC running MATLAB, Psychtoolbox and liblsl-Matlab.

The patch is installed on 4 Raspberry Pi's that are connected over the WiFi network: one is connected to the Xsens receiver, three are connected to the video camera's. The NIRS system receives the LSL messages over the WiFi network. Each Raspberry Pi is running a independent EEGsynth installation, receiving (and responding to) the same LSL messages.
