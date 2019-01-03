# Redis

In the EEGsynth patching (communication) between modules is implemented through the use of the 
open-source [Redis database](http://Redis.io/) which stores 
[attribute-value pairs](https://en.wikipedia.org/wiki/Attribute%E2%80%93value_pair), i.e. a name associated
with a value, such as ('Name', 'John') or ('Height', 1.82). 

A module can put anything it wants into the database, such as ('Heartrate', 92). 
Another module can ask the database to return the value belonging to ('Heartrate'). 
This allows one to create anything from basic 'linear' patches, to complex, many-to-many connections.

Interactions with Redis are specified for each module in their [initialization file](inifile.md). 

Because the Redis database is network-transparent, it can easily be accessed via e.g. other 
programs, so that e.g. EEG can be used to control video games.s 
