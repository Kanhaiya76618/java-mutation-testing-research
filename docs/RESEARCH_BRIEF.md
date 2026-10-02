# Research Brief: Java Mutation Testing for Regression-Test Fault Detection

*Anchored in empirical software engineering literature (2014–2026).*

---

## 1. Foundational Literature & Motivations

1. **Zhao, Zhou & Cohen (2026), "Do Coverage and Mutation Scores of LLM-Generated Test Suites Correlate with Their Effectiveness? (Replicability Study)"**
   - *PACMSE / ISSTA 2026*, arXiv:2607.22880, DOI: 10.1145/3832093.
   - Evaluates whether coverage and mutation scores of LLM-generated test suites track their real fault-detection effectiveness using Defects4J benchmarks.
   - Concludes that while scores provide comparative signals across test suites, proxy-metric improvements degrade in complex production contexts, highlighting the need for rigorous experimental isolation.

2. **Papadakis et al. (2018), "Are mutation scores correlated with real fault detection? a large scale empirical study on the impact of test suite size"**
   - *ICSE 2018*, DOI: 10.1145/3180155.3180183.
   - Demonstrates that reported correlations between mutation score and real-fault detection are often inflated by test-suite size ($SLOC_{test}$), weakening once suite size is controlled.
   - Direct motivation for our size-controlled partial rank correlation ($r_{xy \cdot z}$).

3. **Just et al. (2014), "Are mutants a valid substitute for real faults in software testing?"**
   - *FSE 2014*, DOI: 10.1145/2635868.2635929.
   - Analyzed 357 real faults in 5 open-source Java projects, demonstrating that mutant kill rates are significantly correlated with real fault detection beyond code coverage, driven by the coupling effect.

4. **Foster et al. (2025), "ACH: Automated Code Health at Meta"**
   - *FSE 2025*, Meta Automated Code Health.
   - Details Meta's deployment of targeted mutation analysis to guide automated test generation, targeting specific code health concerns rather than exhaustive combinatorial mutation.

5. **Gopinath, Jensen & Groce (2016), "On the limits of mutation reduction strategies"**
   - *ICSE 2016*, DOI: 10.1145/2884781.2884789.
   - Highlights that random mutant sampling is a formidable baseline, establishing rigorous standards for evaluating operator pruning and selective mutation strategies.

6. **Chekam et al. (2020), "An empirical study on fine-grained assertions and fault revelation"**
   - *IEEE TSE*, DOI: 10.1109/TSE.2019.2941951.
   - Establishes that the fault-detection payoff of mutation testing is predominantly concentrated at high mutation score thresholds with fine-grained assertions.

---

## 2. Methodological Innovation: Method-Level Test Annotation Isolation

Directly executing mutation tools like PITest on buggy source code ($V_{bug}$) aborts execution or yields false mutant kills due to pre-existing assertion failures. Conversely, checking out pre-fix test files against modern production code ($V_{fix}$) triggers compilation errors when tests reference modified APIs.

**Our Protocol:**
- **Pre-Fix Verification:** Confirm that developer-added test methods fail against $V_{bug}$ and pass on $V_{fix}$.
- **Base Suite ($T_{base}$):** Comment out test annotations (`/* @Test */`, `/* @ParameterizedTest */`) on newly added regression test methods, allowing PITest to evaluate a 100% green suite against $V_{fix}$ to produce $MS_{base}$.
- **Augmented Suite ($T_{aug}$):** Restore annotations and recompile, evaluating the complete test suite against $V_{fix}$ to produce $MS_{aug}$.
- **Differential Gain:** $\Delta MS = MS_{aug} - MS_{base}$.

---

## 3. Toolchain & Ecosystem

- **PIT (PITest v1.16.0)**: Bytecode-level Java mutation testing framework.
- **Java Runtime**: OpenJDK 21 LTS (avoiding ASM major version 70 reflection incompatibilities on JDK 26).
- **Target Repository**: Apache Commons Lang.
