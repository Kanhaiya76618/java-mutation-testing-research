# Conference Submission Checklist & Artifact Audit

*Target Venues:*
- **ICSE NIER** (International Conference on Software Engineering — *New Ideas and Emerging Results*)
- **ISSTA Workshop / Tool Demonstration** (International Symposium on Software Testing and Analysis)

---

## 1. Paper Formatting & Metadata Specifications

- [x] **Format Standard:** IEEE Computer Society two-column format (`IEEEtran.cls`) or ACM SIGPLAN format (`acmart.cls`).
- [x] **Page Limit Compliance:** 4–5 pages plus references (standard for NIER / short papers).
- [x] **Title:** *When Does Raising Mutation Score Actually Raise Real-Fault Detection? An Empirical Investigation on Java Ecosystems*
- [x] **Author Details:** Kanhaiya Mehta (`kanhaiyakumar76618@gmail.com`).
- [x] **Anonymization Strategy:**
  - *Single-Blind Submission:* Use author name and public repository link directly as in `paper/main.tex`.
  - *Double-Blind Submission (if required by venue):* Replace author names with *"Anonymous Author(s)"* and replace repository link with an anonymized Zenodo link or anonymous GitHub proxy.

---

## 2. Open Science & Artifact Evaluation Badges

This replication package is designed to qualify for all three ACM/IEEE Artifact Badges:

```
+--------------------+---------------------+--------------------+
| Artifacts Available | Evaluated-Functional| Evaluated-Reusable |
|      [ BADGE ]     |      [ BADGE ]      |     [ BADGE ]      |
+--------------------+---------------------+--------------------+
```

### 1. Artifacts Available
- [x] Repository is publicly accessible: [https://github.com/Kanhaiya76618/java-mutation-testing-research](https://github.com/Kanhaiya76618/java-mutation-testing-research).
- [x] Open-source license applied: `LICENSE` (MIT License).
- [x] Persistent archival metadata defined: `zenodo.json`.
- [x] Standalone artifact bundle created: `scripts/package_zenodo_artifact.sh`.

### 2. Artifacts Evaluated — Functional
- [x] **One-Click Replication:** Running `./scripts/reproduce_all.sh` verifies dependencies, runs unit tests, re-computes statistical tables, and regenerates 300 DPI figures without errors.
- [x] **Continuous Integration:** `.github/workflows/reproduce_and_test.yml` automatically executes on Ubuntu runners to guarantee cross-platform replication.
- [x] **Data Integrity:** `data/processed_results.csv` contains all 18 experimental records across 9 bug pairs, completely matching reported values.

### 3. Artifacts Evaluated — Reusable
- [x] **Modular Harnesses:**
  - `harness/pit_parser.py`: General-purpose parser extracting mutant kill status, operators, and test mapping from any PITest `mutations.xml`.
  - `harness/git_miner.py`: General git miner extracting atomic bug fixes across any git repository.
- [x] **Automated Testing:** Unit test suite in `tests/` achieves 100% pass rate.
- [x] **Clear Documentation:** `docs/REPLICATION_GUIDE.md` details environment prerequisites and reproduction instructions.

---

## 3. Empirical Results & Hypotheses Verification

| Research Question | Metric / Finding | Target Reported Value | Verified in Data |
|---|---|---|---|
| **RQ1 (Predictive Power)** | Partial Correlation ($r_{xy \cdot z}$) | **0.324** | [x] Verified |
| | Vargha-Delaney Effect Size ($\hat{A}_{12}$) | **0.685** (Medium Effect) | [x] Verified |
| | Cliff's Delta ($\delta$) | **0.370** | [x] Verified |
| **RQ2 (Operator Breakdown)** | Math / Arithmetic Sensitivity | **+11.81%** ($\Delta$) | [x] Verified |
| | Conditionals Boundary Sensitivity | **+1.85%** ($\Delta$) | [x] Verified |
| | Void Method Calls Saturation | **0.00%** (Equal 60.56%) | [x] Verified |
| **RQ3 (CI/CD Optimization)** | Mutant Volume Reduction | **63.4%** | [x] Verified |
| | Differential Sensitivity Retention | **91.2%** | [x] Verified |

---

## 4. Pre-Submission Steps

1. **LaTeX Compilation:**
   - Clone repository or export `paper/` folder into Overleaf.
   - Compile using `pdflatex main.tex` and `bibtex main.aux`.
   - Verify layout, figures, and reference formatting.
2. **Zenodo Deposit:**
   - Run `./scripts/package_zenodo_artifact.sh`.
   - Upload `mutation-testing-research-zenodo-artifact.zip` to [zenodo.org](https://zenodo.org).
   - Obtain permanent DOI and insert into paper footnote.
3. **Submit:**
   - Upload generated PDF to conference submission system (HotCRP / EasyChair).
