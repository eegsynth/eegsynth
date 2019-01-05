# A brief history

_(Feel free to skip this and continue with [Modular design](design.md))_

Early development of what later became the EEGsynth was done as part of an interdisciplinary art-science 
initiative [1+1=3](http://oneplusoneisthree.org/), which was on its part a spin-off of a successful international art-research collective
[OuUnPo](http://www.ouunpo.org/). After years of intermittent performances and workshops within 
[OuUnPo](http://www.ouunpo.org/), some of us we were in need of a more concrete and continuous method of exploring a diversity of 
research practices within overlapping themes including neuroscience, music and performance. In November 2014 we first 
used EEG brain activity (of an actor reading a piece by Samuel Beckett) in a performance by transforming it into a score 
for two actors, [staged at the SP Escola de Teatro](http://www.eegsynth.org/?p=51), in Sao Paulo, Brazil.
This proved inspiring, and we started writing some early [MATLAB](https://www.mathworks.com) code, using [FieldTrip](www.fieldtriptoolbox.org)'s architecture and functions for realtime EEG processing. 
We acquired our own [OpenBCI](https://openbci.com/) board (now the Cyton board), which Robert Oostenveld and Stefan Debener 
then implemented in FieldTrip. Artistically, we developed our ideas around providing feedback using sound within 
performative art, especially dance, using electomyography (the measurment of electrical 
signals in muscular control), together with dancer and choreographer [Carima Neusser](http://www.carimaneusser.com/).
This resulted in our first EEGsynth performance in Stockholm, Sweden, with an audience that reflected the 
experimental and interdisciplinary aim of the project, as we discovered that the discussion that the performance could provoke were an inherent, neccecary
and highly satisfying part of such work, and a real meeting-place of professionals of different fields.
Soon after we were awarded us with an [innovation grant](http://www.innovativkultur.se/sv/projektsida/), 
which allowed us some budget to organize private meetings,
public performances as well as start on some [hardware development](http://www.eegsynth.org/?p=312) by Robert. We realized that programming the EEGsynth in MATLAB was unsustainable: to
bridge the gap between artists and scientists we would have to come up with a way to use the EEGsynth that does not 
neccecitate familiarity with MATLAB and the FieldTrip toolbox, and ultimately not a neuroscientist either. We imagined even a 'plug and play' solution in which we
would install the EEGSynth in a [Raspberry-Pi](https://www.raspberrypi.org/) (a small cheap mini-computer the size of a pack of cigarettes) that would 
output control signals for modular synthesizers. This would not be possible with a heavy commercial toolbox such as 
MATLAB. In fact, MATLAB just us not a programming platform that is optimal for real-time processing, at least not in the
way that we started to understand our needs. We needed a lightweight way, where many processes would run in parallel and
communicate with each other in a transparant and flexible way. In other words, we realized we needed something like a 
modular synthesizer, packed in a small box, that could be patched flexibly by non-programmers. Furthermore, it needed 
to be real-time in more than one way: not only would the EEG be analyzed and transformed into signals that could control
live equipment, but we also wanted an interface that did not necessitate typing lines of code, but rather
a more tactile interface with buttons, knobs and sliders. Furthermore, because we were more interested in sound and portability, we did not 
want to rely on a monitor for visual feedback. In short, we reimagined the EEGsynth rewriten in ([Python](https://www.python.org/), running on a [Raspberry Pi], and connected to MIDI controllers. In a way, this was the true 
beginning of the codebase that is now the EEGsynth. Much has happened since, and although the
EEGsynth is not plug-and-play yet, it has in other ways exceeded our expectations. The more clear and modular code 
has made it easier to develop in a distributed way using GitHub, as well as presenting more bite-sized structures for distributed 
development such as in hackathons (see e.g. [Paris Hackathon](http://www.eegsynth.org/?p=377)) and teaching about Brain-Computer-Interfaces (BCIs), 
which we did as a student club at the [Centre of Interdisciplinary research](https://cri-paris.org/criclubs/brain-control-club/). The technical development 
kept following requirements and ideas developed through performances and artistic research within [1+1=3](www.oneplusoneisthree.org). This is the
reason that by now the EEGsynth can interface with most performative equipment using MIDI, CV/gate, DMX, Open Sound 
Controls and ArtNet.  
Importantly, our understanding of the history of experimental music was further enriched when our long-term friend and 
collaborator Samon Takahashi joined us. Were were then even more able to contextualize our work with lectures (e.g. 
during the [Semaine de Cerveau](http://www.eegsynth.org/?p=1084)) or installations on the topic (e.g. at the [Charcot Library](http://www.eegsynth.org/?p=1512)). It became even more clear
what we were doing was another iteration within a fascinating interwoven histories of 
art and science in transducing 'invisible' signals, thereby opening previously closed windows onto reality and experience. 
While the EEGsynth allows artists a foray into science and technology, it has also created many opportunities for scientists 
involved to contribute and express themselves artistically. In fact, the distinction between the two has gradually disappeared, 
and have naturally become two sides of the same coin (see e.g. [Hemispherics](http://www.eegsynth.org/?p=1432)). This is a lot of fun for us, and also 
allows us to interface with the full range of audiences and institutions (see e.g. [here](http://www.eegsynth.org/?p=1103), [here](http://www.eegsynth.org/?p=1516) and [here](https://eegsynth.bandcamp.com/)).
[1+1=3](www.oneplusoneisthree.org) has not been the only artistic collaboration in which the EEGsynth has been used or inspired its development. 
Since 2016, we have been part of an ambition interdisciplinary project called [Cogito in Space](http://www.cogitoinspace.org/) by [Daniela de Paulis](https://www.danieladepaulis.com/). 
In short, the technical aspect
of the project involved the transformation (transduction) of 32-channel EEG into sound in such a way that no information 
is lost. However, no obvious musical aspect is gained, as typically the purpose within 1+1=3. The sound is then transmitted (transduced again) my means of the transmission of radio waves into space using large (25 meter) radio-telescope. While within the other projects we focused 
on creating control signals for sound generation, within [Cogito in Space](http://www.cogitoinspace.org/) we learned about how to directly create sound based on the
EEG, something that will surely feature in future performances. Finally, the EEGsynth is now part of a scientific research project, 
emphasizing the maturity of the project. 

To conclude, technically we have explored some of the scope of the EEGsynth and have seen that the architecture of the EEGsynth has 
indeed achieved the desired flexibility, while further development can occur incrementally by means of the development 
of additional modules. Artistically, we find ourselves in the midst of a field with has a short but dense history.
Many paths in biofeedback and neurofeedback have been identified, some explored in art, and some in science, both littered with
hype and broken promises. Many interesting questions can be found laying wayside, dried out and unanswered, while others have are 
bloated and oversold, resulting in inflation of artistic (and scientific) value. Like in any other field, it is a
question of constructing new meaning and new value from this rubble, and using the achievements of the past to image the 
future. The EEGsynth is developed to be a tool for this construction by interdsciplinary teams such as [1+1=3](www.oneplusoneisthree.org) and [Cogito in Space](http://www.cogitoinspace.org/) .

_Continue reading: [Modular design](design.md)_
