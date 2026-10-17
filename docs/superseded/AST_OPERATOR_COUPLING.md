# AST Node Type & Mutation Operator Coupling Analysis

*Theoretical & Static Analysis Foundation for Budgeted Mutation Selection.*

---

## 1. Motivation: From Heuristic Pruning to Static AST Coupling

Rather than relying on empirical trial-and-error, selective mutation testing can be formalized through Abstract Syntax Tree (AST) grammar nodes. A mutation operator produces a mutant $m$ by transforming a specific AST node $N$ into an altered node $N'$.

To predict whether a candidate mutation site will yield a defect-revealing mutant, we model the probability that a site discriminates real faults:
$$P(\text{Discriminates} \mid N, \text{Context}) = \sigma(\mathbf{w}^T \mathbf{x}_N)$$
where $\mathbf{x}_N$ is a feature vector extracted from the AST and git diff context.

---

## 2. AST Grammar Mapping to PITest Mutators

The table below formalizes the correspondence between Java AST node types (e.g., JavaParser / Eclipse JDT) and PITest bytecode mutation operators:

| AST Grammar Node | Source Code Pattern | PITest Bytecode Operator | Discriminatory Signal in Regression Fixes |
|---|---|---|---|
| **`BinaryExpr` (Relational)** | `a < b`, `x >= y` | `CONDITIONALS_BOUNDARY` | **High (+1.85% $\Delta$)**: Directly models off-by-one fencepost errors. |
| **`BinaryExpr` (Arithmetic)** | `offset + length`, `a * b` | `MATH` | **High (+11.81% $\Delta$)**: Models index arithmetic, array bounds, and scaling calculations. |
| **`UnaryExpr` (Negation)** | `-value`, `~mask` | `INVERT_NEGS` | **Low / Sparse**: Only active on signed numerical algorithms. |
| **`UnaryExpr` (Increment)** | `i++`, `--count` | `INCREMENTS` | **Moderate**: Loops and counter steps. |
| **`MethodCallExpr` (Void)** | `cleanup()`, `notify()` | `VOID_METHOD_CALLS` | **Saturated**: Deleting void calls triggers uncaught exceptions already caught by smoke tests. |
| **`MethodCallExpr` (Return)** | `return obj.get()` | `NULL_RETURNS`, `EMPTY_OBJECT_RETURNS` | **High in Enterprise APIs**: Models null reference omissions. |
| **`ConditionalExpr` (Ternary)** | `c ? t : f` | `REMOVE_CONDITIONALS` | **Moderate**: Conditional branch selection. |

---

## 3. The AST Pre-Filtering Feature Vector

For Continuous Integration pipelines where full AST parsing is available during compilation, each potential mutant site can be scored using cheap static features:

$$\mathbf{x}_N = \begin{bmatrix}
x_{\text{diff}} & \text{Indicator: AST node is inside the git diff hunk} \\
x_{\text{boundary}} & \text{Indicator: Node is a relational boundary comparison} \\
x_{\text{arith}} & \text{Indicator: Node performs pointer/index arithmetic} \\
x_{\text{void\_call}} & \text{Indicator: Node is a standalone void invocation} \\
x_{\text{arid}} & \text{Indicator: Node is in boilerplate (hash/toString/equals)}
\end{bmatrix}$$

### Budgeted Greedy Operator Selection:
Given an execution budget $B$ (e.g., maximum 500 mutants or 30 seconds execution limit):
1. Compute the cost $c(N) = \text{covered tests} \times \text{mean test latency}$.
2. Compute priority ratio $\rho(N) = \frac{P(\text{Discriminates} \mid \mathbf{x}_N)}{c(N)}$.
3. Greedily select top mutants until budget $B$ is reached.

---

## 4. Blind Spots & Failure Modes of Operator Pruning

While pruning to `MATH` and `CONDITIONALS_BOUNDARY` saves >60% computational cost in utility code, peer reviewers must recognize critical failure modes in different software architectures:

1. **Omission Faults:**
   Mutants are syntactic *replacements* or *deletions*. If a real bug is a completely missing validation check or missing defensive `if` statement, standard mutators cannot model the defect unless an adjacent statement is coupled.
2. **Mock-Heavy Enterprise Architecture:**
   While `VOID_METHOD_CALLS` is saturated in stateless utility libraries, in enterprise services (e.g., Spring Boot, security filters, or transactional services), a removed `securityManager.checkPermission()` or `tx.commit()` call is the exact regression bug.
3. **Glue Code & Orchestration:**
   Microservices with minimal mathematical logic have few `MATH` sites; selective pruning in such modules falls back to null-return and exception mutators.
