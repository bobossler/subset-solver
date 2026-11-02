# Software Development Project: Optimal Subset Selection CLI

## Role

You are an experienced software engineer with expertise in Go, Python, Rust, algorithm design, software testing, and performance benchmarking.

Your assignment is to design, implement, test, and compare three command-line applications that solve the same numerical optimization problem.

The applications must behave consistently and produce equivalent results.

Prioritize correctness, maintainability, clear documentation, and reproducible performance measurements.

## 1. Problem Definition

The application accepts two inputs.

### Input 1 — Number List

A comma-separated list of unique, strictly positive integers.

Valid examples:

- `3,5,7,9`
- `3, 5, 7, 9`
- `10,20,30`
- `42`

Invalid examples:

- `3:-5:7` — Invalid delimiter and negative number
- `3,5,5,9` — Duplicate value
- `0,3,5,7` — Zero is not permitted
- `-3,5,7` — Negative numbers are not permitted
- `3:5:7` — Colons are not permitted
- `3;5;7` — Semicolons are not permitted
- `3,5.5,7` — Fractional values are not permitted
- `3,,7` — Empty list element
- `3,5,` — Trailing delimiter
- An empty string — No input values

All numbers must be distinct positive integers.

Whitespace around numbers and commas is permitted.

The original input order must be preserved for output purposes.

### Input 2 — Target Value

A single non-negative integer representing the maximum permitted sum of selected items.

The target may be zero, in which case the optimal subset is empty.

Negative and fractional target values are not permitted.

## 2. Required Computations

### Task A — Calculate the Input Sum

Calculate the sum of every integer in Input 1.

### Task B — Calculate the Optimal Subset

Select a subset of the original input values according to the following objectives, evaluated in strict priority order.

**Primary Objective — Maximum Item Count**

Select the greatest possible number of input items without exceeding the target sum.

**Secondary Objective — Closest Sum**

Among all subsets containing the maximum possible number of items, select the subset whose sum is greatest without exceeding the target.

**Tertiary Objective — Deterministic Tie-Breaking**

When multiple subsets have the same maximum item count and selected sum, choose the subset whose sorted original input indices are lexicographically smallest.

Each input value may be selected at most once.

Because duplicate values are prohibited, every input value uniquely identifies an item.

Preserve the original relative order of selected values in the output.

The algorithm must produce an exact optimal solution for every supported input.

### Example

Input:

    Numbers = [3,5,7,9]
    Target  = 18

Expected:

    Input Sum     = 24
    Selected      = [3,5,9]
    Selected Sum  = 17
    Item Count    = 3
    Difference    = 1

## 3. Input Validation

The application must enforce the following rules.

### Number List Validation

1. Require at least one input value.
2. Accept only comma-separated values.
3. Allow optional whitespace surrounding individual values.
4. Require every value to be a strictly positive integer.
5. Set a common integer range; 64-bit integers (0 through 2^64 − 1).
6. Reject zero.
7. Reject negative values.
8. Reject fractional values.
9. Reject duplicate values.
10. Reject empty elements, including consecutive commas and trailing commas.
11. Reject alphabetic characters and unsupported delimiters.
12. Detect numeric overflow.
13. Preserve the original order of valid input values.

Duplicate detection must compare numerical values, not textual representations. For example, `3,03` must be rejected as a duplicate if leading zeros are accepted.

Document whether leading zeros and explicit plus signs are accepted. Apply the same policy in all three implementations.

### Target Validation

1. Require a target argument.
2. Accept a non-negative integer, including zero.
3. Reject negative values.
4. Reject fractional values.
5. Reject malformed input.
6. Detect numeric overflow.

### Error Handling

For invalid input:

- Display a clear and specific error message to standard error.
- Exit with a nonzero status code.
- Do not produce a misleading partial result.
- Use consistent validation behavior across Go, Python, and Rust.

Document the supported integer range and computational resource limits.

## 4. Command-Line Interface

All three implementations must support the same command-line interface.

Example:

    solver --numbers "3,5,7,9" --target 18

Required arguments:

    --numbers
    --target

Help option:

    --help

### Expected Output

    Input Summary
    -------------
    Numbers:       [3, 5, 7, 9]
    Target:        18
    Input Sum:     24

    Optimal Selection
    -----------------
    Selected:      [3, 5, 9]
    Item Count:    3
    Selected Sum:  17
    Difference:    1

The difference is calculated as:

    Difference = Target - Selected Sum

All three implementations must produce equivalent results and consistent formatting.

When no input item can be selected without exceeding the target, output an empty selection, an item count of zero, and a selected sum of zero.

## 5. Implementation Requirements

Create three independent implementations using the same algorithmic approach.

### Goal 1 — Go

- Use idiomatic modern Go.
- Use only the Go standard library where possible.
- Separate input parsing, validation, optimization, and output formatting.
- Include automated unit tests.
- Provide build and execution instructions.

### Goal 2 — Python

- Use idiomatic modern Python 3.
- Use only the Python standard library.
- Include type hints where appropriate.
- Separate input parsing, validation, optimization, and output formatting.
- Include automated tests using unittest.
- Provide execution instructions.

### Goal 3 — Rust

- Use idiomatic modern stable Rust.
- Prefer the Rust standard library without external crates.
- Separate input parsing, validation, optimization, and output formatting.
- Include automated unit tests.
- Provide build and execution instructions.

All implementations must enforce identical input restrictions.

## 6. Algorithm Requirements

Before implementation:

1. Explain the mathematical optimization problem.
2. Identify suitable exact algorithms.
3. Evaluate brute force, backtracking, dynamic programming, and other relevant techniques.
4. Explain how the restriction to unique positive integers affects algorithm selection.
5. Select an appropriate algorithm.
6. Demonstrate why the algorithm satisfies the optimization priorities.
7. Analyze worst-case time and space complexity.
8. Explain practical limitations involving large lists and target values.

Use the same algorithmic approach in all three languages for a fair comparison.

The algorithm must maximize item count before attempting to maximize the selected sum.

Do not use a greedy approximation as a substitute for the required exact solution.

If the algorithm cannot complete within available resources, report the limitation rather than silently returning a nonoptimal result.

## 7. Testing Requirements

Create a shared set of test cases with identical expected results for all three implementations.

### Functional Tests

Include:

- The original example.
- An exact target match.
- A case where the optimal sum is below the target.
- A case where maximizing item count conflicts with maximizing the sum.
- Multiple equally optimal subsets requiring deterministic tie-breaking.
- A single valid input value.
- A target of zero.
- All input values greater than the target.
- An input sum smaller than the target.
- Unsorted input values.

### Input Validation Tests

Include:

- Negative list values.
- Zero in the list.
- Duplicate list values.
- Numerically equivalent duplicates with different textual representations.
- Colon-separated input.
- Semicolon-separated input.
- Mixed delimiters.
- Decimal values.
- Empty input.
- Consecutive commas.
- Trailing commas.
- Missing required arguments.
- Invalid target values.
- Numeric overflow.
- Whitespace around valid values.

### Correctness Verification

For small inputs, use an independent brute-force reference implementation to verify the optimized algorithm.

Ensure that all three language implementations produce the same selected values, item counts, sums, and differences.

Include commands for executing all automated tests.

## 8. Performance Benchmarking

Benchmark all three implementations using equivalent workloads containing only valid, distinct positive integers.

Test at least:

- Small input lists.
- Medium input lists.
- Large input lists.
- Small target values.
- Large target values.
- Inputs with values distributed across different numerical ranges.
- Cases where most items fit within the target.
- Cases where only a small number of items fit.

Generate reproducible test data using a documented random seed where appropriate.

Measure:

- Execution time.
- Peak memory consumption where practical.
- Process startup overhead separately from core optimization time.
- Build or compilation requirements.
- Result correctness.

Use optimized release builds for Go and Rust where applicable.

Run repeated measurements and report representative results.

Clearly distinguish actual measurements from theoretical expectations.

Do not invent benchmark results.

If the execution environment lacks a required compiler, interpreter, or benchmarking facility, explain the limitation and provide reproducible commands.

## 9. Language Comparison

Compare Go, Python, and Rust using the same input datasets and algorithm.

Evaluate:

1. Algorithm execution performance.
2. Memory efficiency.
3. Source code complexity.
4. Readability and maintainability.
5. Input validation and error handling.
6. Build and deployment requirements.
7. Portability.
8. Standard library support.
9. Suitability for future enhancements.

Present results in a comparison table.

Explain whether performance differences result from language characteristics, runtime overhead, implementation choices, or algorithm behavior.

Recommend the most suitable language for this application under different priorities, including performance, development speed, and maintainability.

## 10. Project Deliverables

Provide a complete project with the following suggested structure:

    subset-solver/
    ├── README.md
    ├── DESIGN.md
    ├── go/
    │   ├── main.go
    │   └── main_test.go
    ├── python/
    │   ├── main.py
    │   └── test_main.py
    ├── rust/
    │   ├── Cargo.toml
    │   └── src/
    │       └── main.rs
    ├── testdata/
    │   └── cases.json
    └── benchmarks/
        └── README.md

Additional files may be included where appropriate.

README.md must document installation, building, execution, testing, input restrictions, and benchmarking.

DESIGN.md must explain the optimization objectives, selected algorithm, correctness argument, complexity, limitations, and implementation decisions.

## 11. Development Workflow

Complete the project in the following stages.

**Stage 1 — Analysis**

Explain the problem, optimization priorities, input restrictions, algorithm choices, complexity, and edge cases.

**Stage 2 — Design**

Propose the shared CLI specification, algorithm, data structures, validation rules, and test strategy.

**Stage 3 — Implementation**

Implement the Go, Python, and Rust applications.

**Stage 4 — Verification**

Execute automated tests where tooling is available, resolve failures, and verify equivalent outputs.

**Stage 5 — Benchmarking**

Measure performance using reproducible workloads and document the execution environment.

**Stage 6 — Final Comparison**

Present the language comparison, conclusions, and recommended implementation.

Do not claim that code was compiled, tested, or benchmarked unless those actions were actually performed.

## 12. Final Expectations

Deliver complete, runnable source code rather than pseudocode.

Use standard libraries wherever possible.

Favor maintainability and correctness over premature optimization.

Explain significant design decisions and trade-offs.

Verify all three implementations against the same reference results wherever possible.

Provide a concise final summary of implementation status, test results, performance findings, and recommendations.

## 13. Approval Gate

Complete Stages 1 and 2 first.

Present:

- The proposed algorithm and justification.
- Time and space complexity.
- The CLI specification.
- Input validation rules.
- The shared test plan.
- Known computational limitations.

**Wait for my explicit approval before generating implementation code.**