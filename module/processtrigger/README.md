# Processtrigger

<<<<<<< HEAD
This module computes basic algebraic operations upon receiving a trigger. The value of the trigger itself is not used, but the values of one or multiple control channels are used.

The `input` section specifies the control values that are used in the computations. The `trigger` section specifies which Redis pub/sub messages trigger a computation. For each trigger, there is a specific section that specifies the computation that is performed.

The output of this module consists of control values that have been updated. Furthermore, when the triggered computations have finished, a copy of the trigger (with the given `prefix`) will be sent.
=======
This module computes basic algebraic operations upon receiving a trigger. The value of the trigger itself can be used in the computation, but also the values of one or multiple control channels.

The `trigger` section specifies which Redis pub/sub messages trigger a computation. The `input` section specifies the control values that are used in the computations. For each trigger, there is a specific section that specifies the computation that is performed.

The output of this module consists of a new trigger with a corresponding control values that is updated. Furthermore, when the triggered computations have finished, a copy of the trigger (with the given `prefix`) will be sent.
>>>>>>> 71c0d3df8c6df126a86dc2ac9929dc17977a9f1c
