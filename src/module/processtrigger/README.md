# Processtrigger

This module computes basic algebraic operations upon receiving a trigger. The value of the trigger itself can be used in the computation, but also the values of one or multiple control channels.

The `trigger` section specifies which Redis pub/sub messages trigger a computation. The `input` section specifies the control values that are used in the computations. For each trigger, there is a specific section that specifies the computation that is performed.

The output of this module consists of a new trigger with a corresponding control values that is updated. Furthermore, when the triggered computations have finished, a copy of the trigger (with the given `prefix`) will be sent.
