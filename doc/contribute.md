# Contributing to EEGsynth development

There are many ways in which one can help develop the EEGsynth, from keeping us informed about
bugs or ambiguoities in the documentation, to writing and debugging code, to developing 
performances and sharing your experiences. We are also looking for financial contributions as
well as scientific collaborations. In that case, please [email us directly](stephen.whitmarsh@gmail.com).

# Modular contribution

To allow the EEGsynth to be easily extendable, we maintain a modular design in which we try to add
either generic functionality in the [EEGsynth library](../lib/EEGsynth.py), or add new modules with
specific functionality that is not yet covered by other modules. When designing another module, one
has to consider whether the same functionality would already be possible by patching together
existing modules.

When contributing code in the form of a new module, one can take an exisiting module as a starting point.
This gives a head start in using the generic skeleton of functions and interfaces that have 
already been developed. Please feel free to contact us with questions on what you would like to develop.
We can probably give you advice to make it easy as possible to reach your goal.   

# Wishlist

What follows are some things that we would like to have support/input on. Ofcourse there are 
many more things, but we don't want to seem greedy :-)

## Precise timing of light effects

The modules that interface with lighting systems over Artnet and DMX work fine for slowly 
changing effects, but are not so good at sudden events. E.g. flashing upon a heartbeat or stroboscopic effects don't really work reliably. 
It would be nice to have better timing control of light effects.

## More affordable EEG hardware

Although we support and use different EEG systems (Gtec, OpenBCI, etc.), none of them are 
really affordable or easy to use. The OpenBCI system is not that expensive, 
but is very much a DIY system that comes as a bare PCB board without enclosure. 
It would be nice to have a low-cost and easy to use EEG system that comes with an enclosure 
including a standard AA battery holder and standard electrode connectors. 



