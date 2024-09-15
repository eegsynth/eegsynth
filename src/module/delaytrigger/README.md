# Delaytrigger

This module computes send delated triggers (Redis key-value pairs) upon receiving a trigger. The value of the original trigger (at the time of triggering) is passed on to the delayed trigger.

The `input` section specifies which Redis pub/sub messages trigger a delayed response. The `delay` section specify the delays (in seconds). The `output` section defined the name of the resultant triggers.
