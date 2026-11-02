# Design

The user approved this algorithm, CLI contract, validation policy, and resource limits before implementation. All production implementations use the same exact approach and standard libraries.

## Mathematical objective

For distinct positive input values a[0..n), choose an increasing index sequence I with sum(a[i] for i in I) <= T. Compare feasible sequences by descending length, descending selected sum, then ascending lexicographic index sequence. This differs from ordinary subset sum: a smaller sum wins when it permits more items. The empty sequence is feasible for every target, including zero.

Positivity makes partial sums monotone, so infeasible partial subsets can be discarded permanently. It also makes the smallest-k prefix characterize feasibility of cardinality k. Uniqueness ensures values identify items but does not remove equal-sum alternatives or the need for index ties.

## Alternatives

Exhaustive enumeration visits 2^m subsets; it is simple and suitable as a small-input oracle. Backtracking can prune by capacity and cardinality bounds, but its worst case is still exponential and highly input-sensitive. Dense dynamic programming has target-dependent pseudo-polynomial cost, impractical for uint64 targets. Sparse dynamic programming avoids allocating the full target range but can retain exponentially many sums; predecessor storage and index ties add complexity. Greedy sorting solves the maximum count alone, but not the maximum sum at that count.

Meet-in-the-middle was selected for predictable bounds in the item count and independence from target magnitude. It trades limited general-search size for support of very large numeric values. There is no fallback approximation or undocumented change of algorithm between languages.

## Algorithm and representation

1. Validate every value and the target, preserving input order. The input total is computed exactly for output.
2. Build eligible `(original_index, value)` pairs for values <= T.
3. If the eligible total <= T, return every eligible index. Empty eligible sets use this path.
4. Reject more than 36 eligible items when search remains necessary.
5. Sort a copy of eligible values. Accumulate the longest prefix whose total <= T; its length is k.
6. Split eligible pairs at floor(m/2). Enumerate feasible subsets of each half, starting with the empty record. Each record contains count, sum, and a local selection mask. Each new item extends only records existing before that item, enforcing single use. Test `value <= target - sum` before adding.
7. Group right records by cardinality. For each sum retain the lexicographically earliest right mask, and sort sums ascending. Go/Rust sort records then compact equal sums; Python deduplicates in dictionaries then sorts the keys. These implement the same mathematical table.
8. For each left record of count c, query the right group k-c by binary search for the largest sum <= T-left_sum. Compare combined candidates by sum and then index order.
9. Map winning bits to original indices, then format values in input order.

Masks have at most 36 significant bits, and half masks at most 18. For two unequal masks of equal cardinality, find the lowest differing bit. The mask containing that bit has the lexicographically smaller index sequence. This comparison is used only at equal cardinality. Eligible order preserves original index order, so comparing eligible masks also compares original index sequences correctly.

Python uses tuples, dictionaries, and `bisect_right`. Go uses record structs, slices, and `sort.Search`. Rust uses record structs, vectors, and `partition_point`. The primary algorithm is identical; storage layouts differ idiomatically and influence benchmark results.

## Correctness

The k smallest positive values have the minimum sum among all k-item subsets. Therefore the longest fitting sorted prefix gives exactly the maximum feasible count. The fast path returns all eligible items when possible, which is the unique maximum-count choice, because excluded items cannot occur in any feasible subset.

Induction on processed items shows enumeration contains every feasible half-subset: each either excludes the next item or extends exactly one earlier subset. Pruning sums above T is safe because all values are positive.

Every feasible k-item subset splits uniquely into a left record and a right record of complementary count. For each left record, the right predecessor query maximizes the feasible combined sum. Thus evaluating every left record finds the global maximum sum at cardinality k.

Discarding a right record with the same count and sum preserves feasibility and objective values. Retaining its lexicographically earliest mask preserves the best possible index tie for every fixed left record. Comparing complete masks then selects the globally earliest optimal sequence. The selected sum is <= T, so subtraction for Difference is safe.

## Complexity and limits

Let n be the full list size and m the eligible size. Parsing and duplicate checks are expected O(n) in item count, plus O(B) text processing for B argument bytes. The all-fit path is O(n) time and space. General search is O(n + m log m + m*2^ceil(m/2)) time and O(n + 2^ceil(m/2)) space. The sorting factor is O(m); binary searches have O(m) comparisons. Masks and subset sums are fixed-width in Go/Rust and bounded-size integers in Python.

At m=36 each half has at most 262,144 records. Feasibility pruning and repeated sums can reduce tables substantially. Python objects carry higher per-record overhead; memory depends on surviving records and allocator behavior. Large targets do not increase table dimensions but may allow more subsets to survive pruning.

The common limits are 4,194,304 argument bytes, 100,000 list items, and 36 eligible items when enumeration is required. These are checked deterministically. OS argument limits can be lower. No timeout-based result is accepted. Allocation failure or external process termination may prevent graceful diagnostics; normal resource-limit checks produce exit 3 and no stdout.

## Numeric and CLI policy

Values and targets are parsed as ASCII unsigned decimal, with surrounding ASCII whitespace trimmed. Leading zeros are accepted and plus signs rejected. Lexical checks precede overflow checks. Duplicates compare numeric values. Number zero is rejected; target zero is accepted. Long leading-zero tokens are supported within the argument limit.

Subset arithmetic never overflows because capacity is checked before addition. Input totals use Go `math/big.Int`, Python integers, and Rust `u128`. A list of 100,000 uint64 values has sum less than 2^81, so `u128` is sufficient. Go's fast-path accumulation stops adding when capacity is exceeded, avoiding overflow without a large integer in the optimizer.

Each application has separate parsing, validation, optimization, and formatting functions. A small custom argument parser makes standard-library flag-parser differences irrelevant. Required options are checked in fixed order (`--numbers`, then `--target`), then list values left to right, then target. A lone `--help` succeeds; mixed help/other arguments fail. Output and errors are shared by contract, including spacing and final newlines. Only a complete successful result is printed.

## Verification and measurement

Shared fixtures cover functional objectives, unsorted input, index ties, all-fit/no-fit cases, full-width values, wide input sums, and malformed arguments/numbers. Native tests use independent exhaustive enumeration. The integration runner also uses a combinations-based oracle with seed 20261102 and checks all three CLI streams and exit statuses. Resource limits exceeding OS launch limits are exercised through library entrypoints.

Benchmarks use saved identical inputs, repeated measurements, separate startup and core timings, and process peak RSS where GNU time is available. Core timing excludes parsing and formatting but includes eligibility filtering, fast paths, sorting, enumeration, and reconstruction. Detailed methods, actual results, and their limitations are in `benchmarks/README.md`.
