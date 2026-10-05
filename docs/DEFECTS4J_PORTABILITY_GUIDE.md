# Defects4J 2.0 Portability Protocol & Scale-Up Guide

*Blueprint for Community Replication across 835 Reproducible Faults.*

---

## 1. Context & Motivation

In our pilot study, we mined and evaluated 9 regression defect pairs in Apache Commons Lang to validate the feasibility of **Method-Level Test Annotation Isolation**. To scale this protocol into a full confirmatory study (achieving the $N \approx 77$–$134$ records demanded by Noether's sample-size power analysis), the benchmark can be directly ported to **Defects4J 2.0** (Just et al., 2014; 2020), which packages **835 reproducible faults across 17 open-source Java projects**.

Crucially, because our protocol executes mutation analysis **exclusively against the fixed revision ($V_{fix}$)** with method annotations masked for $T_{base}$, it avoids the notorious broken-baseline failures that plague traditional execution on buggy revisions.

---

## 2. Automated Portability Workflow

For any project $P$ and bug ID $b$ in Defects4J 2.0:

```
                          [Defects4J Bug Pair (P, b)]
                                      |
                     Checkout Fixed Revision (V_fix):
                     $ defects4j checkout -p P -v ${b}f -w /tmp/run_${b}
                                      |
                     Extract Trigger Tests (T_trigger):
                     $ defects4j export -p tests.trigger
                                      |
            +-------------------------+-------------------------+
            |                                                   |
   [Base Suite: T_base]                                [Augmented Suite: T_aug]
   Apply Annotation Masking:                           Retain Full Test Suite:
   Comment out @Test in T_trigger                      Annotations Active
   $ python3 harness/mask_annotations.py               $ git checkout -- src/test/
            |                                                   |
   Execute PITest on V_fix                             Execute PITest on V_fix
   $ mvn test-compile org.pitest:pitest-maven:mutation $ mvn test-compile org.pitest:pitest-maven:mutation
            |                                                   |
       MS_base (%)                                         MS_aug (%)
            +-------------------------+-------------------------+
                                      |
                            Compute Delta MS (%)
```

### Command Sequence for Automated Evaluation:

```bash
#!/usr/bin/env bash
PROJECT="Csv"
BUG_ID="1"
WORK_DIR="/tmp/d4j_${PROJECT}_${BUG_ID}"

# 1. Checkout fixed version
defects4j checkout -p "${PROJECT}" -v "${BUG_ID}f" -w "${WORK_DIR}"
cd "${WORK_DIR}"

# 2. Identify trigger tests
TRIGGER_TESTS=$(defects4j export -p tests.trigger)
echo "Trigger test methods: ${TRIGGER_TESTS}"

# 3. Mask trigger tests in T_base
for test_method in ${TRIGGER_TESTS}; do
    # Mask @Test and @ParameterizedTest annotations
    sed -i '' -E 's/@Test/\/* @Test *\//g' src/test/java/**/*.java
done

# 4. Run PITest for T_base (100% Green baseline)
mvn compile test-compile org.pitest:pitest-maven:mutation \
    -DmutationThreshold=0 \
    -DoutputFormats=XML

# 5. Restore annotations for T_aug
git checkout -- src/test/

# 6. Run PITest for T_aug
mvn compile test-compile org.pitest:pitest-maven:mutation \
    -DmutationThreshold=0 \
    -DoutputFormats=XML
```

---

## 3. Candidate Project Cohorts in Defects4J 2.0

To ensure architectural diversity beyond utility libraries, candidate projects are grouped into four cohorts:

| Cohort | Projects | Architecture Style | Hypothesized Operator Profile |
|---|---|---|---|
| **Cohort 1: Utility & Math** | `Lang`, `Math`, `Commons-Codec` | Stateless, computational | High `MATH` and `CONDITIONALS_BOUNDARY` sensitivity. |
| **Cohort 2: Parsers & Lexers** | `Csv`, `Gson`, `JacksonCore` | State machine, token buffers | High boundary and state-transition sensitivity. |
| **Cohort 3: Document / DOM** | `Jsoup`, `JFreeChart` | Tree structures, visitor patterns | High null-return and call deletion sensitivity. |
| **Cohort 4: Compilers & Bytecode** | `Closure`, `Mockito` | Complex graph transformations | Combinatorial operator requirements. |

---

## 4. Pre-Registration Protocol for MSR / Registered Reports

By pre-registering this scale-up protocol with frozen analysis scripts (`scripts/analyze_results.py`, `scripts/compare_baselines.py`), the research community can eliminate publication bias and definitively resolve the long-standing debate on mutation score versus real fault detection.
