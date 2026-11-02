# Optimal subset selection

Three independent, standard-library CLI implementations select an exact subset of unique positive integers. They maximize item count, then sum without exceeding the target, then prefer the lexicographically smallest original-index sequence. Selected values retain input order.

## Requirements and execution

Use Go 1.22 or later, Python 3.10 or later, or stable Rust with Cargo (version 1.85 or later, including support for the checked-in version-4 lockfile). Each implementation runs independently; Python is also used for shared verification and benchmark orchestration. No external packages are required.

From the repository root:

```sh
(cd go && go build -o solver .)
./go/solver --numbers "3,5,7,9" --target 18
python3 python/main.py --numbers "3,5,7,9" --target 18
cargo build --release --manifest-path rust/Cargo.toml
./rust/target/release/subset-solver --numbers "3,5,7,9" --target 18
```

All three print:

```text
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
```

Use `--help` alone for usage. Both required arguments accept separate values and can occur in either order. Repeated options, unknown options, positional arguments, and `--numbers=value` forms fail. A known flag where an option's value belongs is reported as a missing value. A negative value is consumed and rejected by numeric validation.

## Input restrictions

- Values: decimal integers from 1 through 18446744073709551615, unique by numerical value.
- Target: decimal integer from 0 through 18446744073709551615.
- Leading zeros are accepted; explicit plus/minus signs are rejected.
- ASCII digits only. Fractions, exponents, alphabetic text, and delimiters other than commas are rejected.
- ASCII space, tab, CR, LF, form feed, and vertical tab are allowed around each numeric token, including the target. Internal whitespace and other Unicode whitespace are rejected.
- Empty lists/elements, consecutive commas, trailing commas, and zero list values are rejected.
- The input sum is exact even when it exceeds 64 bits. It is not itself restricted to uint64.

Exit status is 0 for a result/help, 2 for argument or validation errors, and 3 for computational limits. Errors are identical across languages, go to stderr, and leave stdout empty. Diagnostics use zero-based list indices. Structural argument checks precede numeric checks; list validation proceeds left to right, followed by target validation and optimization. Byte/item limits take precedence over detailed numeric validation.

## Computational limits

Combined argument text is limited to 4 MiB (sum of UTF-8 byte lengths, excluding program name, separators, and terminators), and lists to 100,000 items. Operating-system command-line limits may be smaller; the program cannot validate arguments the OS refuses to launch.

Items above the target are excluded from search. If all remaining items fit, the result is immediate; this covers zero targets and empty eligible sets. Otherwise, at most 36 eligible items are supported. Larger searches return an explicit resource error. This limit applies even to cases another exact algorithm might solve efficiently. No approximation is returned.

Meet-in-the-middle uses exponential space and time in half the eligible item count. The limits are work bounds, not hard memory or time guarantees. Under extreme memory pressure, the operating system or a runtime may terminate a process before it can report an error. Python catches recoverable `MemoryError`; Go and Rust allocation failures may abort. See [DESIGN.md](DESIGN.md).

## Verification

These commands have been executed successfully in the recorded environment:

```sh
(cd go && go build -o solver . && go test ./...)
python3 -m unittest discover -s python -p 'test_*.py'
cargo build --release --manifest-path rust/Cargo.toml
cargo test --manifest-path rust/Cargo.toml
python3 tools/verify.py
```

Go needs a writable build cache; restricted environments can set `GOCACHE` to a writable directory. The shared runner requires the two compiled binaries at the paths above. It checks exact stdout, stderr, exit codes, fixed expected selections, 100 seeded exhaustive-oracle cases, and additional boundary/large-list cases. Each language also has native unit and exhaustive-oracle tests. Shared fixture integers use decimal strings to preserve full precision.

`tools/create_fixtures.py` regenerates the 50 hand-specified fixtures in `testdata/cases.json`; it does not obtain expected answers from a solver. `tools/verify.py` uses a separate combinations-based reference implementation.

## Benchmarks and language choice

See [benchmarks/README.md](benchmarks/README.md) for actual measurements, environment, reproducible commands, and language comparison. Raw results, including individual samples, are in `benchmarks/results.json`. Dataset generation uses seed 20261102. Build times are not included in runtime measurements.

## Repository layout

- `go/`: argument parsing, validation, optimizer, formatting, native tests, and optional core timing test.
- `python/`: equivalent solver and unittest tests.
- `rust/`: solver library, small CLI entrypoint, unit tests, and core timing example.
- `testdata/cases.json`: common success, error, and help fixtures.
- `tools/`: fixture generation and cross-language verification.
- `benchmarks/`: saved inputs, generator, measurement runner, results, and comparison.
