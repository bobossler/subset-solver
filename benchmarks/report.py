"""Render the measured tables from results.json without inventing data."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
r=json.loads((ROOT/'results.json').read_text())
e=r['environment']
lines=['# Benchmarks and language comparison','',
       'These are actual measurements from one Linux machine. They describe these implementations and workloads, not universal language rankings. Raw individual samples are retained in [results.json](results.json).','',
       '## Environment','',
       f"- Platform: {e['platform']}",f"- CPU: {e['cpu']}; {e['logical_cpus']} logical CPUs available",
       f"- Go: {e['go']}",f"- Python: {e['python'].splitlines()[0]}",f"- Rust: {e['rust']}",
       '- Go used the default optimized build (`go build`); Rust used `--release`. Python used the standard interpreter. No external packages were installed.','',
       '## Reproduction','',
       'Run from the repository root, after building the CLI binaries and running verification:','',
       '```sh','python3 benchmarks/generate.py','mkdir -p benchmarks/bin',
       '(cd go && go test -c -o ../benchmarks/bin/go-core)',
       'cargo build --release --examples --manifest-path rust/Cargo.toml',
       'python3 benchmarks/run.py','python3 benchmarks/report.py','```','',
       'The measurement runner currently targets Linux (`/proc/cpuinfo`); GNU `/usr/bin/time` supplies optional peak RSS. A writable Go build cache is required to compile the timing driver. Build commands, test commands, and the benchmark commands above were executed successfully. Compilation duration was not benchmarked.','',
       'Seed: **20261102**. Saved files in `data/` are the canonical common inputs. `workloads.json` records item counts, targets, and core repetition counts. Regenerating uses Python standard-library `random.Random`; keeping the saved files avoids generator-version differences.','',
       '## Method','',
       'Startup measurements launch `--help` ten times and include process creation, runtime initialization, argument handling, and help output. They are a startup baseline, not a pure runtime initialization measurement. CLI measurements launch a full solve five times after one warm-up. They include parsing, validation, optimization, formatting, process creation, and captured output.','',
       'Core measurements exclude parsing, validation, and formatting. They include eligibility filtering, fast paths, sorting, subset enumeration, search, and reconstruction. Each sample averages the workload-specific number of iterations; three such samples are collected. Go uses an opt-in compiled test driver, Rust a release example, and Python a direct imported call. Repeated calls include ordinary allocation and runtime memory-management costs.','',
       'Reported times are medians; min/max and all samples are in results.json. Peak RSS is one separate full CLI run per workload, measured in KiB by GNU time; it includes the runtime and allocator, not just algorithm tables. No startup subtraction is applied. The process was not pinned to a CPU, frequency was not controlled, and other system activity can affect results. Sub-millisecond results should be interpreted cautiously.','',
       'Every measured CLI result is checked against the same expected complete output. Small/medium workloads are independently exhaustively checked, including the 24-item medium case. Larger benchmark expectations come from the Python solver and are checked against both independent native implementations; they do not constitute an exhaustive proof for large inputs. Core drivers check selected count and sum; the separate CLI verification checks full selection and tie behavior.','',
       '## Measured startup baseline','', '| Language | Median ms | Min–max ms |','|---|---:|---:|']
for language,v in r['startup'].items():
    lines.append(f"| {language} | {v['median_seconds']*1000:.3f} | {v['min_seconds']*1000:.3f}–{v['max_seconds']*1000:.3f} |")
lines += ['', '## Workloads','', '| Workload | Items | Target | Selected count | Description |', '|---|---:|---:|---:|---|']
descriptions={
'small':'Values 1–99; roughly half the total fits',
'medium':'Values 1–10,000; half-total target',
'large_search':'36 searchable values up to 1,000,000; target 60% of total',
'large_values':'30 values near 10^17; large 64-bit target',
'few_fit':'36 input items; only the four smallest are eligible',
'most_fit':'30 items; target excludes only the smallest from the full total',
'large_list_all_fit':'10,000 items; all-fit fast path',
'large_list_small_target':'10,000 items; target 10, no eligible values'}
for w in r['workloads']:
    lines.append(f"| {w['name']} | {w['n']} | {w['target']} | {w['selected_count']} | {descriptions[w['name']]} |")
for title,kind,scale in [('Core optimization, median milliseconds','core',1000),('Complete CLI, median milliseconds','cli',1000),('Peak process RSS, KiB','rss',1)]:
    lines += ['', '## '+title, '', '| Workload | Go | Python | Rust |','|---|---:|---:|---:|']
    for w in r['workloads']:
        values=[]
        for language in ['Go','Python','Rust']:
            v=w['languages'][language]
            values.append(str(v.get('peak_rss_kib','unavailable')) if kind=='rss' else f"{v[kind]['median_seconds']*scale:.4f}")
        lines.append('| '+w['name']+' | '+' | '.join(values)+' |')
lines += ['', '## Interpretation and comparison','',
          'Rust had the lowest measured core time, CLI time, and RSS for every saved workload. On the 36-item search, median core times were approximately 22.4 ms Rust, 75.1 ms Go, and 303.5 ms Python; full-process RSS was approximately 20.1, 35.2, and 91.2 MiB respectively. Python startup dominated tiny searches. Large-list fast paths show parsing, formatting, and process overhead can exceed optimization time.','',
          'All implementations use the same exact algorithm. Native record layout and arithmetic avoid Python tuple/dictionary/integer object overhead. Rust and Go also differ in sorting interfaces, vector/slice growth, retained allocations, and garbage collection; these measurements do not isolate the cost of any single mechanism. Rust sorts concrete records with a generic comparator; Go uses reflection-based `sort.Slice`. Python uses dictionaries before sorting rather than sorting and compacting records. These implementation choices contribute alongside language/runtime differences.','',
          '| Criterion | Go | Python | Rust |','|---|---|---|---|',
          '| Measured optimization and memory | Between Rust and Python here | Slowest and largest RSS here | Fastest and smallest RSS here |',
          '| Source complexity | Straightforward explicit slices and errors | Most compact solver; easy to inspect | More explicit types, ownership, and result handling |',
          '| Readability and maintenance | Simple control flow; gofmt and built-in tests | Concise; type hints help maintain invariants | Compiler enforces ownership and many invariants; higher learning cost |',
          '| Validation and error handling | Custom parser, checked uint64 conversion, explicit errors | Custom parser, range checks required despite unbounded integers | Custom parser, checked uint64 parsing, Result-based errors |',
          '| Build/deployment | Compiler needed to build; deploy target binary | Interpreter needed; no compilation step | Cargo/compiler needed to build; deploy target binary |',
          '| Portability | Cross-compilation support; OS/architecture-specific binary | Portable source on supported Python versions | Many targets; target toolchains/linkers may be needed |',
          '| Standard library support | Sorting, tests, big integers, JSON | Sorting, bisect, integers, unittest, JSON | Sorting, tests, u128; shared JSON fixtures handled by external Python runner |',
          '| Future enhancements | Good fit for operational CLI features and concurrency | Fastest iteration for exploring algorithms and analyses | Strong fit for compact tables and detailed memory control |','',
          'Choose Rust when measured speed and memory use are the priority and the team is comfortable with it. Choose Python for development speed, algorithm experiments, and workloads well within the search limit. Choose Go for a maintainable compiled CLI with simple deployment and a smaller language surface. Increasing the search limit substantially requires reconsidering the algorithm or storage strategy in every language; switching languages alone does not remove exponential growth.','',
          'No build-time benchmark, statistical significance claim, cross-machine comparison, or extrapolated unsupported-input performance is presented.']
(ROOT/'README.md').write_text('\n'.join(lines)+'\n')
print('Rendered benchmarks/README.md')
