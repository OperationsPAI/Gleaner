# RQ2: Impact on Root Cause Analysis

This table shows the performance of different sampling algorithms on RCA effectiveness.
**Sampling Rates**: 0.005, 0.010, 0.100
**Metrics**: MRR (Mean Reciprocal Rank), AC@1 (Accuracy@1), AC@3 (Accuracy@3)

## Nezha Results

| Sampler            | Rate  | MRR    | AC@1   | AC@3   |
| ------------------ | ----- | ------ | ------ | ------ |
| gleaner            | 0.005 | 0.5667 | 0.1005 | 0.2392 |
| gleaner            | 0.010 | 0.6012 | 0.1722 | 0.4354 |
| gleaner            | 0.100 | 0.5392 | 0.1053 | 0.3493 |
| random             | 0.005 | 0.6350 | 0.0861 | 0.1483 |
| random             | 0.010 | 0.5691 | 0.0526 | 0.1435 |
| random             | 0.100 | 0.5508 | 0.0909 | 0.2010 |
| sieve              | 0.005 | 0.5422 | 0.0622 | 0.1627 |
| sieve              | 0.010 | 0.5582 | 0.0957 | 0.2105 |
| sieve              | 0.100 | 0.4796 | 0.0861 | 0.1579 |
| sifter             | 0.005 | 0.5473 | 0.0383 | 0.1579 |
| sifter             | 0.010 | 0.4477 | 0.0239 | 0.1483 |
| sifter             | 0.100 | 0.4633 | 0.0766 | 0.2297 |
| tracepicker        | 0.005 | 0.4839 | 0.0622 | 0.1675 |
| tracepicker        | 0.010 | 0.4645 | 0.0670 | 0.1722 |
| tracepicker        | 0.100 | 0.4495 | 0.0526 | 0.1866 |
| trastrainer        | 0.005 | 0.5137 | 0.0431 | 0.1627 |
| trastrainer        | 0.010 | 0.5917 | 0.0861 | 0.2153 |
| trastrainer        | 0.100 | 0.4573 | 0.0622 | 0.1722 |
| trastrainer_no_met | 0.005 | 0.6553 | 0.0813 | 0.1818 |
| trastrainer_no_met | 0.010 | 0.5693 | 0.0813 | 0.2249 |
| trastrainer_no_met | 0.100 | 0.5570 | 0.1005 | 0.2440 |

## ShapleyIQ Results

| Sampler            | Rate  | MRR    | AC@1   | AC@3   |
| ------------------ | ----- | ------ | ------ | ------ |
| gleaner            | 0.005 | 0.5917 | 0.4402 | 0.5191 |
| gleaner            | 0.010 | 0.6466 | 0.5144 | 0.5837 |
| gleaner            | 0.100 | 0.6303 | 0.4928 | 0.5622 |
| random             | 0.005 | 0.4834 | 0.2273 | 0.3589 |
| random             | 0.010 | 0.4882 | 0.2919 | 0.3995 |
| random             | 0.100 | 0.5855 | 0.4402 | 0.5455 |
| sieve              | 0.005 | 0.5119 | 0.3134 | 0.4474 |
| sieve              | 0.010 | 0.5182 | 0.3397 | 0.4498 |
| sieve              | 0.100 | 0.6132 | 0.4689 | 0.5598 |
| sifter             | 0.005 | 0.4753 | 0.2344 | 0.3589 |
| sifter             | 0.010 | 0.4958 | 0.2871 | 0.4306 |
| sifter             | 0.100 | 0.5735 | 0.4211 | 0.5263 |
| tracepicker        | 0.005 | 0.5654 | 0.3995 | 0.5167 |
| tracepicker        | 0.010 | 0.5385 | 0.3708 | 0.4880 |
| tracepicker        | 0.100 | 0.5760 | 0.4330 | 0.5048 |
| trastrainer        | 0.005 | 0.4598 | 0.2177 | 0.3684 |
| trastrainer        | 0.010 | 0.4330 | 0.2249 | 0.3445 |
| trastrainer        | 0.100 | 0.4211 | 0.2344 | 0.3852 |
| trastrainer_no_met | 0.005 | 0.4569 | 0.1938 | 0.3206 |
| trastrainer_no_met | 0.010 | 0.4559 | 0.2225 | 0.3349 |
| trastrainer_no_met | 0.100 | 0.5574 | 0.3947 | 0.5311 |

## Summary

### Nezha Best Performers
**Rate 0.005:**
- Best MRR: trastrainer_no_met (0.6553)
- Best AC@1: gleaner (0.1005)
- Best AC@3: gleaner (0.2392)

**Rate 0.010:**
- Best MRR: gleaner (0.6012)
- Best AC@1: gleaner (0.1722)
- Best AC@3: gleaner (0.4354)

**Rate 0.100:**
- Best MRR: trastrainer_no_met (0.5570)
- Best AC@1: gleaner (0.1053)
- Best AC@3: gleaner (0.3493)

### ShapleyIQ Best Performers
**Rate 0.005:**
- Best MRR: gleaner (0.5917)
- Best AC@1: gleaner (0.4402)
- Best AC@3: gleaner (0.5191)

**Rate 0.010:**
- Best MRR: gleaner (0.6466)
- Best AC@1: gleaner (0.5144)
- Best AC@3: gleaner (0.5837)

**Rate 0.100:**
- Best MRR: gleaner (0.6303)
- Best AC@1: gleaner (0.4928)
- Best AC@3: gleaner (0.5622)
