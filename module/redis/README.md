# Redis module

The purpose of this module is to start the Redis key-value database database. This allows communication between (most) other modules, which use put/get and pub/sub to send and receive messages. Compared to the patching of an analog synthesizer with cables, the Redis module allows all other modules to be flexibly linked to each other.

This module should be started prior to all other modules.
