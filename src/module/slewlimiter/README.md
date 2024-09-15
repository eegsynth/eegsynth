# Slew Limiter Module

The purpose of this module is to limit how fast control values from Redis can change. This can be used to smooth an otherwise rapidly changing noisy signal, e.g., for the [vumeter](../vumeter) module, or to implement portamento.

A `learning_rate` of 0 causes the control values to remain fixed at the historical value. With a `learning_rate` of 1, the control value changes instantly.

With a `delay` of 0.05 seconds, the output value is updated 20 times per second.

With a `learning_rate` of 0.1, each update results in an output that consists for 90% of the old value, and 10% of the new value.

The half-time of the exponential filter can be computed as

```
halftime = delay * log10(0.5) / log10(1-learning_rate)
```

## When running with with 50 ms delay, i.e., updating 20 times per second

| delay (s)  | learning_rate  | halftime (s) |
|------------|----------------|--------------|
| 0.05       | 0.500          | 0.0500       |
| 0.05       | 0.200          | 0.1553       |
| 0.05       | 0.100          | 0.3289       |
| 0.05       | 0.050          | 0.6757       |
| 0.05       | 0.020          | 1.7155       |
| 0.05       | 0.010          | 3.4484       |
| 0.05       | 0.005          | 6.9141       |
| 0.05       | 0.002          | 17.3113      |
| 0.05       | 0.001          | 34.6400      |

## When running with with 10 ms delay, i.e., updating 100 times per second

| delay (s)  | learning_rate  | halftime (s) |
|------------|----------------|--------------|
| 0.01       | 0.500          | 0.0100       |
| 0.01       | 0.200          | 0.0311       |
| 0.01       | 0.100          | 0.0658       |
| 0.01       | 0.050          | 0.1351       |
| 0.01       | 0.020          | 0.3431       |
| 0.01       | 0.010          | 0.6897       |
| 0.01       | 0.005          | 1.3828       |
| 0.01       | 0.002          | 3.4623       |
| 0.01       | 0.001          | 6.9280       |

## When running with with 5 ms delay, i.e., updating 200 times per second

| delay (s)  | learning_rate  | halftime (s) |
|------------|----------------|--------------|
| 0.005      | 0.500          | 0.0050       |
| 0.005      | 0.200          | 0.0155       |
| 0.005      | 0.100          | 0.0329       |
| 0.005      | 0.050          | 0.0676       |
| 0.005      | 0.020          | 0.1715       |
| 0.005      | 0.010          | 0.3448       |
| 0.005      | 0.005          | 0.6914       |
| 0.005      | 0.002          | 1.7311       |
| 0.005      | 0.001          | 3.4640       |
