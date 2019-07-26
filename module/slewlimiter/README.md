# Slew Limiter Module

The purpose of this module is to limit how fast control values from Redis can change. This can be used to smooth an otherwise rapidly changing noisy signal, e.g. for the [vumeter](../vumeter) module, or to implement portamento.

A `learning_rate` of 0 causes the control values to remain fixed at the historical value. With a `learning_rate` of 1, the control value changes instantly.

With a `delay` of 0.05 seconds, the output value is updated 20 times per second. With a `learning_rate` of 0.1, this results in an output that consists for approximately 10% of the previous values, and 90% of the most recent values.

The half-time of the exponential filter can be computed as

```
halftime = delay * log10(0.5) / log10(1-learning_rate)
```

| delay (s)  | learning_rate  | halftime (s) |
|------------|----------------|--------------|
| 0.05       | 0.2            | 0.15         |
| 0.05       | 0.1            | 0.33         |
| 0.05       | 0.034          | 1.0          |
| 0.05       | 0.010          | 3.4          |
| 0.05       | 0.0034         | 10.2         |
| 0.05       | 0.0010         | 34.6         |
