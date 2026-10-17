# Data comparison: original CSV (v1) vs. re-measured data (v2)

- v1: `data/processed_results.csv` (9 bug pairs)
- v2: `data/v2/runs.csv` (10 bug pairs), `operators.csv`, `skipped.csv`
- v2 mutation score = PIT's own definition (detected / total, timeouts count as detected); killed-only = KILLED / total, the v1 definition.

## 1. Candidates

| # | Commit | Change | In v1 | In v2 | v2 skip reason |
|---|---|---|---|---|---|
| 0 | `e992a498` | LANG-1834 Fix Fraction reduction for Integer.MIN_VALUE  | yes | yes |  |
| 1 | `45f08d9e` | Fix TypeUtils.toString() recursion and bound handling o | no | no | the fix commit adds no new test methods |
| 2 | `e1ce120c` | Fix TypeUtils.toString() recursion and bound handling o | no | yes |  |
| 3 | `d8f4116d` | Fix MethodUtils.invokeMethod on instances of non-public | yes | yes |  |
| 4 | `e213b85c` | Fix Fraction.add and subtract for operands not in lowes | yes | yes |  |
| 5 | `df1e9189` | Fix TypeUtils.isAssignable() for wildcards with multipl | yes | yes |  |
| 6 | `e4380908` | Fix DurationFormatUtils.formatPeriod() calculation when | yes | yes |  |
| 7 | `0edbb4ae` | fix int overflow in Conversion count and position bound | yes | yes |  |
| 8 | `1d6ef29c` | Fix CharRange.contains for negated argument ranges (#17 | yes | yes |  |
| 9 | `8d9ada12` | Fix typos in Javadoc and example comments (#1774) | no | no | the fix commit adds no new test methods |
| 10 | `4ee32aa5` | Fix low surrogate false match in containsAny/containsNo | yes | yes |  |
| 11 | `10f44214` | Fix spurious overflow in Fraction.multiplyBy for unredu | no | no | the fix commit adds no new test methods |
| 12 | `9288e2c9` | Fix the overflow bound direction in Instants.toMillisSi | yes | yes |  |
| 13 | `a1c12e6d` | Fix two Javadoc errors in StringUtils (#1763) | no | no | the fix commit adds no new test methods |

## 2. Suite size and mutation score per pair

| Commit | Tests base→aug (v1) | Tests base→aug (v2) | MS base→aug (v1) | MS base→aug (v2) | ΔMS v1 | ΔMS v2 | ΔMS v2 killed-only | Added tests failing on V_bug |
|---|---|---|---|---|---|---|---|---|
| `0edbb4ae` | 0 → 0 | 54 → 55 | 89.23 → 89.57 | 89.57 → 89.91 | +0.34 | +0.34 | +0.34 | 1 of 1 |
| `1d6ef29c` | 0 → 0 | 18 → 19 | 69.23 → 92.31 | 69.23 → 92.31 | +23.08 | +23.08 | +23.08 | 1 of 1 |
| `4ee32aa5` | 0 → 0 | 93 → 96 | 5.58 → 6.31 | 12.25 → 13.31 | +0.73 | +1.05 | +1.05 | 3 of 3 |
| `9288e2c9` | 0 → 0 | 26 → 28 | 71.43 → 92.86 | 71.43 → 92.86 | +21.43 | +21.43 | +21.43 | 2 of 2 |
| `d8f4116d` | 0 → 0 | 59 → 67 | 80.60 → 83.19 | 80.60 → 83.19 | +2.59 | +2.59 | +2.59 | 5 of 7 |
| `df1e9189` | 0 → 0 | 410 → 411 | 67.72 → 68.54 | 67.88 → 68.71 | +0.82 | +0.83 | +0.83 | 1 of 1 |
| `e1ce120c` | — → — | 411 → 429 | — → — | 65.25 → 69.17 | — | +3.92 | +3.92 | 17 of 18 |
| `e213b85c` | 0 → 0 | 36 → 37 | 74.50 → 75.07 | 79.37 → 79.94 | +0.57 | +0.57 | +0.29 | 1 of 1 |
| `e4380908` | 0 → 0 | 47 → 48 | 79.52 → 79.92 | 85.94 → 86.35 | +0.40 | +0.40 | +0.40 | 1 of 1 |
| `e992a498` | 683 → 683 | 38 → 39 | 80.00 → 80.00 | 80.00 → 80.29 | +0.00 | +0.29 | +0.00 | 1 of 1 |

## 3. Operator columns of v1 vs. mutants that exist in v2 (augmented suite)

v1 wrote 0.00 when a class had no mutants of an operator. v2 counts only mutants that exist.

| Commit | ConditionalsBoundaryMutator | NegateConditionalsMutator | MathMutator | VoidMethodCallMutator | InvertNegsMutator |
|---|---|---|---|---|---|
| `0edbb4ae` | v1 67.6 · v2 46/68 | v1 0.0 · v2 none | v1 93.2 · v2 275/295 | v1 100.0 · v2 4/4 | v1 0.0 · v2 none |
| `1d6ef29c` | v1 91.7 · v2 11/12 | v1 0.0 · v2 none | v1 100.0 · v2 2/2 | v1 100.0 · v2 1/1 | v1 0.0 · v2 none |
| `4ee32aa5` | v1 4.8 · v2 15/187 | v1 0.0 · v2 none | v1 7.9 · v2 23/189 | v1 0.0 · v2 0/27 | v1 0.0 · v2 0/1 |
| `9288e2c9` | v1 0.0 · v2 0/1 | v1 0.0 · v2 none | v1 0.0 · v2 none | v1 0.0 · v2 none | v1 0.0 · v2 none |
| `d8f4116d` | v1 90.9 · v2 10/11 | v1 0.0 · v2 none | v1 90.9 · v2 10/11 | v1 100.0 · v2 8/8 | v1 0.0 · v2 none |
| `df1e9189` | v1 75.0 · v2 12/16 | v1 0.0 · v2 none | v1 0.0 · v2 none | v1 25.0 · v2 2/8 | v1 0.0 · v2 none |
| `e1ce120c` | v1 — · v2 10/14 | v1 — · v2 none | v1 — · v2 none | v1 — · v2 1/8 | v1 — · v2 none |
| `e213b85c` | v1 16.7 · v2 5/30 | v1 0.0 · v2 none | v1 83.3 · v2 65/72 | v1 60.0 · v2 3/5 | v1 75.0 · v2 15/16 |
| `e4380908` | v1 83.3 · v2 10/12 | v1 0.0 · v2 none | v1 76.6 · v2 43/47 | v1 100.0 · v2 7/7 | v1 0.0 · v2 none |
| `e992a498` | v1 16.7 · v2 5/30 | v1 80.4 · v2 none | v1 83.6 · v2 66/73 | v1 60.0 · v2 3/5 | v1 75.0 · v2 15/16 |

## 4. Mutators PIT generated in v2 (all bugs, augmented suite)

| Mutator | Operator | Mutants | Detected | Bugs with this mutator |
|---|---|---|---|---|
| BooleanFalseReturnValsMutator | FALSE_RETURNS | 129 | 79 | 7 |
| BooleanTrueReturnValsMutator | TRUE_RETURNS | 188 | 118 | 7 |
| ConditionalsBoundaryMutator | CONDITIONALS_BOUNDARY | 381 | 124 | 10 |
| EmptyObjectReturnValsMutator | EMPTY_RETURNS | 367 | 83 | 9 |
| IncrementsMutator | INCREMENTS | 61 | 15 | 8 |
| InvertNegsMutator | INVERT_NEGS | 33 | 30 | 3 |
| MathMutator | MATH | 689 | 484 | 7 |
| NullReturnValsMutator | NULL_RETURNS | 268 | 217 | 10 |
| PrimitiveReturnsMutator | PRIMITIVE_RETURNS | 193 | 171 | 7 |
| RemoveConditionalMutator_EQUAL_ELSE | REMOVE_CONDITIONALS_EQUAL_ELSE | 1215 | 618 | 10 |
| RemoveConditionalMutator_EQUAL_IF | REMOVE_CONDITIONALS_EQUAL_IF | 1218 | 652 | 10 |
| RemoveConditionalMutator_ORDER_ELSE | REMOVE_CONDITIONALS_ORDER_ELSE | 381 | 192 | 10 |
| RemoveConditionalMutator_ORDER_IF | REMOVE_CONDITIONALS_ORDER_IF | 381 | 183 | 10 |
| SwitchMutator | SwitchMutator | 7 | 5 | 3 |
| VoidMethodCallMutator | VOID_METHOD_CALLS | 73 | 29 | 9 |

## 5. Mutants newly detected by the added tests (T_aug minus T_base), per operator

Raw counts summed over all v2 pairs. This is descriptive: adding tests can only add detections.

| Operator | Mutants (all pairs) | Newly detected | Pairs with ≥1 newly detected | Newly detected per pair |
|---|---|---|---|---|
| CONDITIONALS_BOUNDARY | 381 | 3 | 2 | 1d6ef29c: 2, e1ce120c: 1 |
| EMPTY_RETURNS | 367 | 5 | 1 | e1ce120c: 5 |
| FALSE_RETURNS | 129 | 3 | 3 | 1d6ef29c: 1, df1e9189: 1, e1ce120c: 1 |
| INCREMENTS | 61 | 0 | 0 |  |
| INVERT_NEGS | 33 | 0 | 0 |  |
| MATH | 689 | 14 | 4 | 0edbb4ae: 1, 1d6ef29c: 2, 4ee32aa5: 9, e213b85c: 2 |
| NULL_RETURNS | 268 | 0 | 0 |  |
| PRIMITIVE_RETURNS | 193 | 1 | 1 | 9288e2c9: 1 |
| REMOVE_CONDITIONALS_EQUAL_ELSE | 1215 | 28 | 5 | 1d6ef29c: 8, 4ee32aa5: 9, 9288e2c9: 1, d8f4116d: 2, e1ce120c: 8 |
| REMOVE_CONDITIONALS_EQUAL_IF | 1218 | 25 | 7 | 1d6ef29c: 5, 4ee32aa5: 5, 9288e2c9: 1, d8f4116d: 4, df1e9189: 2, e1ce120c: 7, e992a498: 1 |
| REMOVE_CONDITIONALS_ORDER_ELSE | 381 | 6 | 4 | 0edbb4ae: 2, 1d6ef29c: 2, e1ce120c: 1, e4380908: 1 |
| REMOVE_CONDITIONALS_ORDER_IF | 381 | 3 | 2 | 1d6ef29c: 2, e1ce120c: 1 |
| SwitchMutator | 7 | 0 | 0 |  |
| TRUE_RETURNS | 188 | 4 | 2 | 1d6ef29c: 2, df1e9189: 2 |
| VOID_METHOD_CALLS | 73 | 0 | 0 |  |
