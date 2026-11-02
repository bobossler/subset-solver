# Benchmarks and language comparison

These are actual measurements from one Linux machine. They describe these implementations and workloads, not universal language rankings. Raw individual samples are retained in [results.json](results.json).

## Environment

- Platform: Linux-7.2.6-76070206-generic-x86_64-with-glibc2.39
- CPU: Intel(R) Core(TM) i3-10110U CPU @ 2.10GHz; 4 logical CPUs available
- Go: go version go1.27.3 linux/amd64
- Python: 3.12.3 (main, Aug 31 2026, 10:18:26) [GCC 13.3.0]
- Rust: rustc 1.97.0 (2d8144b78 2026-07-07)
- Go used the default optimized build (`go build`); Rust used `--release`. Python used the standard interpreter. No external packages were installed.

## Reproduction

Run from the repository root, after building the CLI binaries and running verification:

```sh
python3 benchmarks/generate.py
mkdir -p benchmarks/bin
(cd go && go test -c -o ../benchmarks/bin/go-core)
cargo build --release --examples --manifest-path rust/Cargo.toml
python3 benchmarks/run.py
python3 benchmarks/report.py
```

The measurement runner currently targets Linux (`/proc/cpuinfo`); GNU `/usr/bin/time` supplies optional peak RSS. A writable Go build cache is required to compile the timing driver. Build commands, test commands, and the benchmark commands above were executed successfully. Compilation duration was not benchmarked.

Seed: **20261102**. Saved files in `data/` are the canonical common inputs. `workloads.json` records item counts, targets, and core repetition counts. Regenerating uses Python standard-library `random.Random`; keeping the saved files avoids generator-version differences.

## Method

Startup measurements launch `--help` ten times and include process creation, runtime initialization, argument handling, and help output. They are a startup baseline, not a pure runtime initialization measurement. CLI measurements launch a full solve five times after one warm-up. They include parsing, validation, optimization, formatting, process creation, and captured output.

Core measurements exclude parsing, validation, and formatting. They include eligibility filtering, fast paths, sorting, subset enumeration, search, and reconstruction. Each sample averages the workload-specific number of iterations; three such samples are collected. Go uses an opt-in compiled test driver, Rust a release example, and Python a direct imported call. Repeated calls include ordinary allocation and runtime memory-management costs.

Reported times are medians; min/max and all samples are in results.json. Peak RSS is one separate full CLI run per workload, measured in KiB by GNU time; it includes the runtime and allocator, not just algorithm tables. No startup subtraction is applied. The process was not pinned to a CPU, frequency was not controlled, and other system activity can affect results. Sub-millisecond results should be interpreted cautiously.

Every measured CLI result is checked against the same expected complete output. Small/medium workloads are independently exhaustively checked, including the 24-item medium case. Larger benchmark expectations come from the Python solver and are checked against both independent native implementations; they do not constitute an exhaustive proof for large inputs. Core drivers check selected count and sum; the separate CLI verification checks full selection and tie behavior.

## Measured startup baseline

| Language | Median ms | Min–max ms |
|---|---:|---:|
| Go | 1.283 | 1.154–1.424 |
| Python | 22.387 | 21.490–22.541 |
| Rust | 0.771 | 0.715–1.083 |

## Workloads

| Workload | Items | Target | Selected count | Description |
|---|---:|---:|---:|---|
| small | 12 | 300 | 8 | Values 1–99; roughly half the total fits |
| medium | 24 | 68571 | 16 | Values 1–10,000; half-total target |
| large_search | 36 | 12617136 | 26 | 36 searchable values up to 1,000,000; target 60% of total |
| large_values | 30 | 1500000006879033822 | 15 | 30 values near 10^17; large 64-bit target |
| few_fit | 36 | 98046 | 1 | 36 input items; only the four smallest are eligible |
| most_fit | 30 | 15393088 | 29 | 30 items; target excludes only the smallest from the full total |
| large_list_all_fit | 10000 | 5009284402 | 10000 | 10,000 items; all-fit fast path |
| large_list_small_target | 10000 | 10 | 0 | 10,000 items; target 10, no eligible values |

## Core optimization, median milliseconds

| Workload | Go | Python | Rust |
|---|---:|---:|---:|
| small | 0.0166 | 0.0523 | 0.0033 |
| medium | 0.9111 | 3.6699 | 0.2351 |
| large_search | 75.1185 | 303.4644 | 22.3660 |
| large_values | 10.5965 | 58.4334 | 3.8733 |
| few_fit | 0.0009 | 0.0070 | 0.0005 |
| most_fit | 8.0523 | 25.7975 | 2.1984 |
| large_list_all_fit | 0.2084 | 1.7575 | 0.0212 |
| large_list_small_target | 0.0089 | 0.3791 | 0.0056 |

## Complete CLI, median milliseconds

| Workload | Go | Python | Rust |
|---|---:|---:|---:|
| small | 1.2840 | 22.1229 | 0.7634 |
| medium | 2.1990 | 25.3577 | 1.1200 |
| large_search | 79.0652 | 338.2032 | 22.5931 |
| large_values | 13.2425 | 84.7907 | 5.0595 |
| few_fit | 1.2849 | 20.8357 | 0.8175 |
| most_fit | 10.4443 | 48.2254 | 3.2765 |
| large_list_all_fit | 6.6030 | 40.0070 | 3.9277 |
| large_list_small_target | 5.1881 | 36.7015 | 3.3568 |

## Peak process RSS, KiB

| Workload | Go | Python | Rust |
|---|---:|---:|---:|
| small | 2444 | 11100 | 2120 |
| medium | 3340 | 12288 | 2324 |
| large_search | 36020 | 93348 | 20620 |
| large_values | 7436 | 22244 | 4548 |
| few_fit | 2316 | 11264 | 2116 |
| most_fit | 7516 | 21144 | 4532 |
| large_list_all_fit | 6028 | 14212 | 3260 |
| large_list_small_target | 4236 | 13872 | 3088 |

## Interpretation and comparison

Rust had the lowest measured core time, CLI time, and RSS for every saved workload. On the 36-item search, median core times were approximately 22.4 ms Rust, 75.1 ms Go, and 303.5 ms Python; full-process RSS was approximately 20.1, 35.2, and 91.2 MiB respectively. Python startup dominated tiny searches. Large-list fast paths show parsing, formatting, and process overhead can exceed optimization time.

All implementations use the same exact algorithm. Native record layout and arithmetic avoid Python tuple/dictionary/integer object overhead. Rust and Go also differ in sorting interfaces, vector/slice growth, retained allocations, and garbage collection; these measurements do not isolate the cost of any single mechanism. Rust sorts concrete records with a generic comparator; Go uses reflection-based `sort.Slice`. Python uses dictionaries before sorting rather than sorting and compacting records. These implementation choices contribute alongside language/runtime differences.

| Criterion | Go | Python | Rust |
|---|---|---|---|
| Measured optimization and memory | Between Rust and Python here | Slowest and largest RSS here | Fastest and smallest RSS here |
| Source complexity | Straightforward explicit slices and errors | Most compact solver; easy to inspect | More explicit types, ownership, and result handling |
| Readability and maintenance | Simple control flow; gofmt and built-in tests | Concise; type hints help maintain invariants | Compiler enforces ownership and many invariants; higher learning cost |
| Validation and error handling | Custom parser, checked uint64 conversion, explicit errors | Custom parser, range checks required despite unbounded integers | Custom parser, checked uint64 parsing, Result-based errors |
| Build/deployment | Compiler needed to build; deploy target binary | Interpreter needed; no compilation step | Cargo/compiler needed to build; deploy target binary |
| Portability | Cross-compilation support; OS/architecture-specific binary | Portable source on supported Python versions | Many targets; target toolchains/linkers may be needed |
| Standard library support | Sorting, tests, big integers, JSON | Sorting, bisect, integers, unittest, JSON | Sorting, tests, u128; shared JSON fixtures handled by external Python runner |
| Future enhancements | Good fit for operational CLI features and concurrency | Fastest iteration for exploring algorithms and analyses | Strong fit for compact tables and detailed memory control |

Choose Rust when measured speed and memory use are the priority and the team is comfortable with it. Choose Python for development speed, algorithm experiments, and workloads well within the search limit. Choose Go for a maintainable compiled CLI with simple deployment and a smaller language surface. Increasing the search limit substantially requires reconsidering the algorithm or storage strategy in every language; switching languages alone does not remove exponential growth.

No build-time benchmark, statistical significance claim, cross-machine comparison, or extrapolated unsupported-input performance is presented.
