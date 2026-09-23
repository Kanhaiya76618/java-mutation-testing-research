# Research Brief: Java Mutation Testing for Regression-Test Fault Detection

*Anchored in 2023–2026 software engineering literature.*

---

## 1. Foundational Paper

> **Zhao, Zhou & Cohen (2026), "Do Coverage and Mutation Scores of LLM-Generated Test Suites Correlate with Their Effectiveness? (Replicability Study)"**
> *PACMSE / ISSTA 2026*, arXiv:2607.22880, DOI: 10.1145/3832093.

### Key Discoveries:
1. **Suite size is not a dominant confounder** for LLM-generated tests across models (contrasting Inozemtseva & Holmes 2014 on human tests).
2. **Coverage and mutation scores remain informative** when comparing models in regression/bug-free contexts, but degrade when code-under-test contains unknown faults.
3. **Open Problem #2 & #4 explicitly identified:**
   - Under what conditions do proxy-metric improvements (coverage, mutation) translate to higher real-bug detection?
   - How project-specific are these correlations across real-world Java ecosystems?

---

## 2. Supporting Landscape (2023–2026)

- **Alshahwan et al. (FSE 2025)**: *Mutation-Guided LLM-based Test Generation at Meta*. Mutation testing deployed in production to iteratively prompt LLMs for missing test cases.
- **Sowmyadevi & Alphy (MethodsX 2026)**: *GNN-based mutation-aware regression test ordering*. Uses execution traces + PIT mutants to guide regression test prioritization.
- **Flaky-Test Interactions (Parry et al. 2025, IEEE TSE)**: Non-deterministic tests can cause false mutant kills or mask genuine survivors.
- **Dakhel et al. (IST 2024)**: *Effective test generation using pre-trained LLMs and mutation testing*.

---

## 3. Toolchain & Benchmarks

- **PIT (PITest)**: State-of-the-art bytecode mutation testing tool for Java.
- **Defects4J v3.0**: Real bug dataset for Java (Just et al.).
- **JaCoCo**: Industry standard Java bytecode coverage tool.
