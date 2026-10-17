# Superseded documents

These documents belong to the first version of this study (September to early October 2026).
They are kept only for transparency. **Do not cite or reuse their results.**

Why they are superseded:

- Their numbers come from `data/processed_results.csv` (v1), which has known data errors: suite
  sizes recorded as 0, a LANG-1834 base row copied from the augmented row, and operator scores of
  0% for operators that had no mutants. See `../DATA_V1_VS_V2.md`.
- Several results (mutant-budget reduction, sensitivity retention, leave-one-bug-out accuracy,
  execution times, the random-sampling and PITest DEFAULTS baselines) were typed into scripts or
  documents, or simulated, instead of being computed from measured data.
- They rely on comparing T_base with T_aug. Because T_aug is T_base plus tests, that comparison
  shows a mutation-score gain for any added tests, so it cannot show that mutation score tracks
  bug detection. See `../PITFALL_ANALYSIS.md`.
- `DEFECT_TAXONOMY_MAPPING.md` describes the wrong classes for several commits
  (for example, `d8f4116d` fixes `MethodUtils`, not `NumberUtils`).
- Several citations had wrong titles or authors.

Current results: `../PITFALL_ANALYSIS.md`, `../SUBSET_ANALYSIS.md`, `../DATA_V1_VS_V2.md` and
`../../paper/main.tex`, all generated from `data/v2/` and `data/raw/`.
