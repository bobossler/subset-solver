# Repository Guidelines

## Project Status and Structure

The project is implemented in three independent languages using standard libraries. `initial-prompt.md` is the original specification; `README.md` documents the current CLI, requirements, and verified commands; `DESIGN.md` explains the approved exact algorithm and correctness argument.

- `go/main.go`: argument parsing, validation, optimization, formatting, and CLI entrypoint. `go/main_test.go` contains native correctness tests; `go/benchmark_test.go` contains resource tests and an opt-in core timing driver. `go/go.mod` defines the module.
- `python/main.py`: equivalent solver functions and CLI entrypoint. `python/test_main.py` contains unittest tests.
- `rust/src/lib.rs`: solver functions and native tests. `rust/src/main.rs` is the CLI entrypoint. `rust/examples/core.rs` is the core timing driver. Keep `Cargo.toml` and `Cargo.lock` together.
- `testdata/cases.json`: shared success, validation, help, and resource-error fixtures. Numeric fixture values are decimal strings to preserve full precision.
- `tools/create_fixtures.py`: regenerates hand-specified shared fixtures without using a solver for expected selections.
- `tools/verify.py`: runs all three CLIs against fixtures and an independent combinations-based brute-force oracle.
- `benchmarks/generate.py`, `workloads.json`, and `data/`: deterministic workload generation, metadata, and saved common inputs.
- `benchmarks/run.py`: repeated startup, CLI, core timing, and optional process RSS measurements. `results.json` stores raw samples and environment information; `report.py` renders `benchmarks/README.md`.
- Generated binaries, Rust `target/`, benchmark `bin/`, and Python caches are ignored by Git.

Keep parsing, validation, optimization, and formatting separate in each implementation. All three must remain independently runnable.

## Development Workflow

The original analysis/design approval gate in `initial-prompt.md` was completed: the user explicitly approved the meet-in-the-middle design, CLI policies, and resource limits before implementation. Routine fixes, tests, and documentation updates within that design do not require repeating the initial approval gate. Explain material algorithm or contract changes and obtain approval before replacing the approved design or limits.

Preserve identical behavior across languages: maximize item count first, selected sum second, then choose the lexicographically smallest increasing original-index sequence. Preserve input order in output. Never substitute an approximation or emit a partial result after failure.

When changing behavior, update all three implementations, shared fixtures, and relevant documentation together. Rebuild native binaries before running shared verification; the runner executes binaries, not source files.

## Exact Algorithm and Invariants

Filter out values greater than the target, retaining original indices. If all eligible values fit, return them immediately, including empty selections for zero targets or no eligible values. Otherwise:

1. Find the maximum feasible cardinality k using the longest fitting prefix of sorted eligible values.
2. Split eligible items into halves and enumerate feasible subsets, recording count, sum, and a bitmask.
3. Group right-half subsets by count and sort by sum, retaining the lexicographically earliest mask for equal count and sum.
4. For each left subset, binary-search the complementary-count right group for the largest fitting sum. Compare complete candidates by sum and then original indices.

Positivity makes capacity pruning safe. Extend only records that existed before processing the current item, so each item is used at most once. Check `value <= target - sum` before addition to prevent overflow. For equal-cardinality masks, the mask containing the lowest differing bit wins the index tie; this rule must not be used to compare different cardinalities.

For n input items and m eligible items, general-search time is O(n + m log m + m*2^ceil(m/2)), and space is O(n + 2^ceil(m/2)), plus argument-text processing. Go/Rust sort and compact right records; Python deduplicates by sum before sorting keys. Preserve the same mathematical search despite idiomatic storage differences.

## Shared CLI and Validation Contract

- Required arguments: `--numbers VALUE --target VALUE`, in either order. Accept separate option/value arguments only. `--help` alone succeeds. Reject unknown/repeated options, positional arguments, equals forms, and missing values.
- Values are unique positive uint64 integers; target is a non-negative uint64 integer. Maximum: 18446744073709551615.
- Accept ASCII decimal digits and leading zeros; reject explicit plus/minus signs, fractions, exponents, unsupported delimiters, and non-ASCII digits.
- Trim only ASCII space, tab, CR, LF, form feed, and vertical tab around tokens. Reject internal whitespace and other Unicode whitespace.
- Reject empty lists/elements, trailing/consecutive commas, zero list values, and numerical duplicates such as `3,03`. Preserve original input order.
- Perform structural argument checks first, then list validation left to right, then target validation, then optimization. Check required options in the order `--numbers`, `--target`. Byte/item limits precede detailed numeric validation. Diagnostics use zero-based indices.
- Calculate the full input sum exactly, even beyond uint64: Go uses `math/big.Int`, Python uses integers, and Rust uses `u128`. The item limit keeps the Rust total below 2^81.
- Preserve exact stdout formatting, stderr messages, and final newlines across languages. Print a result only after validation and optimization succeed.
- Exit codes: 0 success/help, 2 invalid arguments/input, 3 computational resource limits. Errors go to stderr and leave stdout empty.

## Resource Limits

The approved common limits are 4,194,304 combined argument bytes (UTF-8 lengths, excluding the executable name, separators, and terminators), 100,000 input items, and 36 eligible items when enumeration is needed. The all-fit fast path is allowed above 36 eligible items. Do not apply the search cap to the original list length or silently raise it.

At 36 eligible items, each half has at most 262,144 subset records. These are work bounds, not guaranteed memory/time ceilings. OS command-line limits can prevent process launch below the application's argument limit; exercise larger limits via library entrypoints. Python catches recoverable `MemoryError`; Go/Rust allocation failures or OS termination may prevent graceful diagnostics.

## Build, Run, and Test

Documented requirements: Go 1.22+, Python 3.10+, and Rust/Cargo 1.85+ (including support for the version-4 lockfile). Minimum versions were not separately tested. Recorded successful execution used Go 1.27.3, Python 3.12.3, and Rust 1.97.0 on Linux; see benchmark metadata for the full environment.

Run from the repository root:

```sh
(cd go && go build -o solver . && go test ./...)
./go/solver --numbers "3,5,7,9" --target 18
python3 python/main.py --numbers "3,5,7,9" --target 18
python3 -m unittest discover -s python -p 'test_*.py'
cargo build --release --manifest-path rust/Cargo.toml
cargo test --manifest-path rust/Cargo.toml
./rust/target/release/subset-solver --numbers "3,5,7,9" --target 18
python3 tools/verify.py
```

Go requires a writable build cache. In restricted environments, use an authorized writable cache or the environment's approval mechanism for cache access. Do not misdiagnose a cache permission failure as a source failure.

Format Go with `gofmt` and Rust with `cargo fmt --manifest-path rust/Cargo.toml`; check Rust formatting with `cargo fmt --check --manifest-path rust/Cargo.toml`. Use four-space Python indentation, type hints, and `snake_case`; use idiomatic language naming elsewhere. Prefer standard libraries and avoid introducing dependencies without a concrete need.

## Testing Guidelines and Verified Baseline

Use Go's testing package (`*_test.go`), Python unittest (`test_*.py`), and Rust `#[test]` tests. No coverage threshold is established. Preserve an independent brute-force oracle rather than deriving expected answers from the optimized implementation.

The completed baseline passed native tests in all three languages and shared verification of 50 fixtures, 100 seeded brute-force cases, and six additional CLI checks across all languages. Additional checks cover option order, long leading zeros, large-list fast paths, and a known-answer search at the 36-item boundary. Resource limits above OS launch limits are tested through library entrypoints. Treat these counts as historical evidence, not immutable requirements.

Important regressions include count priority (`[2,3,9]`, target 9 selects `[2,3]`), original-index ties (`[4,1,3,2]`, target 5 selects `[4,1]`), zero targets, all/no eligible items, uint64 boundaries, input totals above uint64, numerical duplicates, malformed CLI arguments, and resource-limit boundaries. Check complete selected sequences, counts, sums, differences, stdout, stderr, and exit status.

## Benchmark Workflow and Interpretation

After building both CLI binaries and passing correctness checks:

```sh
python3 benchmarks/generate.py
mkdir -p benchmarks/bin
(cd go && go test -c -o ../benchmarks/bin/go-core)
cargo build --release --examples --manifest-path rust/Cargo.toml
python3 benchmarks/run.py
python3 benchmarks/report.py
```

Seed 20261102 generates eight saved workloads covering small/medium/36-item searches, large values, few/most items fitting, and 10,000-item fast paths. Saved inputs are canonical; generator versions can affect reproduction. Generation and measurement overwrite saved datasets/results, so run them intentionally. The current runner targets Linux through `/proc/cpuinfo`; GNU `/usr/bin/time` optionally supplies peak RSS.

Use optimized Go builds and Rust release builds. Report startup separately from complete CLI and core optimization. The current harness uses ten help launches, five measured CLI launches after a warm-up, and three core samples with workload-specific iterations. Peak RSS is a separate single CLI run and includes runtime/allocator overhead. Core timing excludes parsing/validation/formatting but includes filtering, allocation, sorting, enumeration, search, and reconstruction. Core drivers check count/sum; CLI verification checks the complete selection.

Raw samples, environment, and limitations belong in `results.json` and the benchmark report. Small/medium benchmark expectations are independently exhaustively checked; larger workloads use cross-language agreement rather than exhaustive verification. Do not claim build-time measurements, statistical significance, or universal language rankings from this harness. Review the generated report's interpretation when rerunning: `report.py` contains narrative tied to the original measurements.

In the recorded 36-item run, median core times were approximately 22.4 ms Rust, 75.1 ms Go, and 303.5 ms Python. Rust also had the lowest measured RSS across saved workloads. These observations reflect concrete storage/sorting/allocation choices as well as language runtimes. They are not acceptance thresholds. Switching languages does not remove exponential search growth.

## Commit and Pull Request Guidelines

Use concise, imperative commit messages describing one coherent change. PRs should explain behavior, affected implementations, validation actually performed, and limitations; link relevant issues when available. Keep shared fixtures and documentation synchronized with CLI changes. Report only builds, tests, and benchmarks actually executed, distinguishing historical results from fresh verification. Do not commit generated executables or caches.
