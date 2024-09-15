# Signal Plotting Module

This module plots the ExG signals from the FieldTrip buffer in real-time.

It also includes some simple preprocessing and filtering options, but be aware that the filters may have edge artifacts due to the block-wise processing. It is better to use the [preprocessing](../preprocessing) module for filtering, which does the filtering continuously.
