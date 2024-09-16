# Rhythms

The EEGsynth can be used in a variety of ways in creating or modulating rhythms using the generateclock or heartbeat module, combined with the clockdivider, clockmultiplier and sequencer modules.

There are many interesting resources available online:

- Flash implementation of [Euclidean rhythms](https://www.hisschemoller.com/blog/2011/euclidean-rhythms/)
- [African polyrhythms](https://mynoise.net/NoiseMachines/polyrhythmBeatGenerator.php)
- [Code](https://codegolf.stackexchange.com/questions/49221/generating-euclidean-rhythms)) for generating the Euclidean rhythms

Some interesting hardware modules are:

- [Knight's Gallop](http://www.shakmatmodular.com/products/kg.html)

The following Python code can be used to generate a list of Euclidean rhythms to be used in the [sequencer module](../src/module/sequencer).

```
f=lambda n,k,a='1',b='0':n-k<2and a*k+b*(n-k)or[f(n-k,k,a+b,b),f(k,n-k,a+b,a)][2*k>n]

for n in range(1,16+1):
  for k in range(1,n+1):

    print 'euclidian_%d_%d = %s' % (n, k, " ".join(f(n,k)))`

    euclidian_1_1 = 1
    euclidian_2_1 = 1 0
    euclidian_2_2 = 1 1
    euclidian_3_1 = 1 0 0
    euclidian_3_2 = 1 1 0
    euclidian_3_3 = 1 1 1
    euclidian_4_1 = 1 0 0 0
    euclidian_4_2 = 1 0 1 0
    euclidian_4_3 = 1 1 1 0
    euclidian_4_4 = 1 1 1 1
    euclidian_5_1 = 1 0 0 0 0
    euclidian_5_2 = 1 0 1 0 0
    euclidian_5_3 = 1 0 1 0 1
    euclidian_5_4 = 1 1 1 1 0
    euclidian_5_5 = 1 1 1 1 1
    euclidian_6_1 = 1 0 0 0 0 0
    euclidian_6_2 = 1 0 0 1 0 0
    euclidian_6_3 = 1 0 1 0 1 0
    euclidian_6_4 = 1 0 1 1 0 1
    euclidian_6_5 = 1 1 1 1 1 0
    euclidian_6_6 = 1 1 1 1 1 1
    euclidian_7_1 = 1 0 0 0 0 0 0
    euclidian_7_2 = 1 0 0 1 0 0 0
    euclidian_7_3 = 1 0 1 0 1 0 0
    euclidian_7_4 = 1 0 1 0 1 0 1
    euclidian_7_5 = 1 0 1 1 0 1 1
    euclidian_7_6 = 1 1 1 1 1 1 0
    euclidian_7_7 = 1 1 1 1 1 1 1
    euclidian_8_1 = 1 0 0 0 0 0 0 0
    euclidian_8_2 = 1 0 0 0 1 0 0 0
    euclidian_8_3 = 1 0 0 1 0 0 1 0
    euclidian_8_4 = 1 0 1 0 1 0 1 0
    euclidian_8_5 = 1 0 1 1 0 1 1 0
    euclidian_8_6 = 1 0 1 1 1 0 1 1
    euclidian_8_7 = 1 1 1 1 1 1 1 0
    euclidian_8_8 = 1 1 1 1 1 1 1 1
    euclidian_9_1 = 1 0 0 0 0 0 0 0 0
    euclidian_9_2 = 1 0 0 0 1 0 0 0 0
    euclidian_9_3 = 1 0 0 1 0 0 1 0 0
    euclidian_9_4 = 1 0 1 0 1 0 1 0 0
    euclidian_9_5 = 1 0 1 0 1 0 1 0 1
    euclidian_9_6 = 1 0 1 1 0 1 1 0 1
    euclidian_9_7 = 1 0 1 1 1 0 1 1 1
    euclidian_9_8 = 1 1 1 1 1 1 1 1 0
    euclidian_9_9 = 1 1 1 1 1 1 1 1 1
    euclidian_10_1 = 1 0 0 0 0 0 0 0 0 0
    euclidian_10_2 = 1 0 0 0 0 1 0 0 0 0
    euclidian_10_3 = 1 0 0 1 0 0 1 0 0 0
    euclidian_10_4 = 1 0 0 1 0 1 0 0 1 0
    euclidian_10_5 = 1 0 1 0 1 0 1 0 1 0
    euclidian_10_6 = 1 0 1 1 0 1 0 1 1 0
    euclidian_10_7 = 1 0 1 1 0 1 1 0 1 1
    euclidian_10_8 = 1 0 1 1 1 1 0 1 1 1
    euclidian_10_9 = 1 1 1 1 1 1 1 1 1 0
    euclidian_10_10 = 1 1 1 1 1 1 1 1 1 1
    euclidian_11_1 = 1 0 0 0 0 0 0 0 0 0 0
    euclidian_11_2 = 1 0 0 0 0 1 0 0 0 0 0
    euclidian_11_3 = 1 0 0 0 1 0 0 0 1 0 0
    euclidian_11_4 = 1 0 0 1 0 0 1 0 0 1 0
    euclidian_11_5 = 1 0 1 0 1 0 1 0 1 0 0
    euclidian_11_6 = 1 0 1 0 1 0 1 0 1 0 1
    euclidian_11_7 = 1 0 1 1 0 1 1 0 1 1 0
    euclidian_11_8 = 1 0 1 1 1 0 1 1 1 0 1
    euclidian_11_9 = 1 0 1 1 1 1 0 1 1 1 1
    euclidian_11_10 = 1 1 1 1 1 1 1 1 1 1 0
    euclidian_11_11 = 1 1 1 1 1 1 1 1 1 1 1
    euclidian_12_1 = 1 0 0 0 0 0 0 0 0 0 0 0
    euclidian_12_2 = 1 0 0 0 0 0 1 0 0 0 0 0
    euclidian_12_3 = 1 0 0 0 1 0 0 0 1 0 0 0
    euclidian_12_4 = 1 0 0 1 0 0 1 0 0 1 0 0
    euclidian_12_5 = 1 0 0 1 0 1 0 0 1 0 1 0
    euclidian_12_6 = 1 0 1 0 1 0 1 0 1 0 1 0
    euclidian_12_7 = 1 0 1 1 0 1 0 1 1 0 1 0
    euclidian_12_8 = 1 0 1 1 0 1 1 0 1 1 0 1
    euclidian_12_9 = 1 0 1 1 1 0 1 1 1 0 1 1
    euclidian_12_10 = 1 0 1 1 1 1 1 0 1 1 1 1
    euclidian_12_11 = 1 1 1 1 1 1 1 1 1 1 1 0
    euclidian_12_12 = 1 1 1 1 1 1 1 1 1 1 1 1
    euclidian_13_1 = 1 0 0 0 0 0 0 0 0 0 0 0 0
    euclidian_13_2 = 1 0 0 0 0 0 1 0 0 0 0 0 0
    euclidian_13_3 = 1 0 0 0 1 0 0 0 1 0 0 0 0
    euclidian_13_4 = 1 0 0 1 0 0 1 0 0 1 0 0 0
    euclidian_13_5 = 1 0 0 1 0 1 0 0 1 0 1 0 0
    euclidian_13_6 = 1 0 1 0 1 0 1 0 1 0 1 0 0
    euclidian_13_7 = 1 0 1 0 1 0 1 0 1 0 1 0 1
    euclidian_13_8 = 1 0 1 1 0 1 0 1 1 0 1 0 1
    euclidian_13_9 = 1 0 1 1 0 1 1 0 1 1 0 1 1
    euclidian_13_10 = 1 0 1 1 1 0 1 1 1 0 1 1 1
    euclidian_13_11 = 1 0 1 1 1 1 1 0 1 1 1 1 1
    euclidian_13_12 = 1 1 1 1 1 1 1 1 1 1 1 1 0
    euclidian_13_13 = 1 1 1 1 1 1 1 1 1 1 1 1 1
    euclidian_14_1 = 1 0 0 0 0 0 0 0 0 0 0 0 0 0
    euclidian_14_2 = 1 0 0 0 0 0 0 1 0 0 0 0 0 0
    euclidian_14_3 = 1 0 0 0 0 1 0 0 0 0 1 0 0 0
    euclidian_14_4 = 1 0 0 0 1 0 0 1 0 0 0 1 0 0
    euclidian_14_5 = 1 0 0 1 0 0 1 0 0 1 0 0 1 0
    euclidian_14_6 = 1 0 0 1 0 1 0 1 0 0 1 0 1 0
    euclidian_14_7 = 1 0 1 0 1 0 1 0 1 0 1 0 1 0
    euclidian_14_8 = 1 0 1 1 0 1 0 1 0 1 1 0 1 0
    euclidian_14_9 = 1 0 1 1 0 1 1 0 1 1 0 1 1 0
    euclidian_14_10 = 1 0 1 1 1 0 1 1 0 1 1 1 0 1
    euclidian_14_11 = 1 0 1 1 1 1 0 1 1 1 1 0 1 1
    euclidian_14_12 = 1 0 1 1 1 1 1 1 0 1 1 1 1 1
    euclidian_14_13 = 1 1 1 1 1 1 1 1 1 1 1 1 1 0
    euclidian_14_14 = 1 1 1 1 1 1 1 1 1 1 1 1 1 1
    euclidian_15_1 = 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0
    euclidian_15_2 = 1 0 0 0 0 0 0 1 0 0 0 0 0 0 0
    euclidian_15_3 = 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0
    euclidian_15_4 = 1 0 0 0 1 0 0 0 1 0 0 0 1 0 0
    euclidian_15_5 = 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0
    euclidian_15_6 = 1 0 0 1 0 1 0 0 1 0 1 0 0 1 0
    euclidian_15_7 = 1 0 1 0 1 0 1 0 1 0 1 0 1 0 0
    euclidian_15_8 = 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1
    euclidian_15_9 = 1 0 1 1 0 1 0 1 1 0 1 0 1 1 0
    euclidian_15_10 = 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1
    euclidian_15_11 = 1 0 1 1 1 0 1 1 1 0 1 1 1 0 1
    euclidian_15_12 = 1 0 1 1 1 1 0 1 1 1 1 0 1 1 1
    euclidian_15_13 = 1 0 1 1 1 1 1 1 0 1 1 1 1 1 1
    euclidian_15_14 = 1 1 1 1 1 1 1 1 1 1 1 1 1 1 0
    euclidian_15_15 = 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
    euclidian_16_1 = 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
    euclidian_16_2 = 1 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0
    euclidian_16_3 = 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 0
    euclidian_16_4 = 1 0 0 0 1 0 0 0 1 0 0 0 1 0 0 0
    euclidian_16_5 = 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 0
    euclidian_16_6 = 1 0 0 1 0 1 0 0 1 0 0 1 0 1 0 0
    euclidian_16_7 = 1 0 0 1 0 1 0 1 0 0 1 0 1 0 1 0
    euclidian_16_8 = 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0
    euclidian_16_9 = 1 0 1 1 0 1 0 1 0 1 1 0 1 0 1 0
    euclidian_16_10 = 1 0 1 1 0 1 0 1 1 0 1 1 0 1 0 1
    euclidian_16_11 = 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1
    euclidian_16_12 = 1 0 1 1 1 0 1 1 1 0 1 1 1 0 1 1
    euclidian_16_13 = 1 0 1 1 1 1 0 1 1 1 1 0 1 1 1 1
    euclidian_16_14 = 1 0 1 1 1 1 1 1 1 0 1 1 1 1 1 1
    euclidian_16_15 = 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 0
    euclidian_16_16 = 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
```
