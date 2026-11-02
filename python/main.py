"""Exact maximum-cardinality subset solver (standard library only)."""
from bisect import bisect_right
import sys

MAX_U64 = (1 << 64) - 1
MAX_ITEMS = 100_000
MAX_BYTES = 4 * 1024 * 1024
WHITESPACE = " \t\r\n\f\v"
HELP = 'Usage: solver --numbers "3,5,7,9" --target 18\n       solver --help\n'


class SolverError(Exception):
    def __init__(self, message: str, code: int = 2):
        super().__init__(message)
        self.code = code


def parse_args(args: list[str]) -> tuple[str, str] | None:
    if sum(len(arg.encode("utf-8")) for arg in args) > MAX_BYTES:
        raise SolverError("argument text exceeds 4194304 bytes", 3)
    if args == ["--help"]:
        return None
    values: dict[str, str] = {}
    i = 0
    while i < len(args):
        flag = args[i]
        if flag not in ("--numbers", "--target"):
            raise SolverError(f"unknown argument: {flag}")
        if flag in values:
            raise SolverError(f"repeated argument: {flag}")
        if i + 1 == len(args) or args[i + 1] in ("--numbers", "--target", "--help"):
            raise SolverError(f"missing value for {flag}")
        values[flag] = args[i + 1]
        i += 2
    for flag in ("--numbers", "--target"):
        if flag not in values:
            raise SolverError(f"missing required argument: {flag}")
    return values["--numbers"], values["--target"]


def parse_integer(text: str, label: str) -> int:
    token = text.strip(WHITESPACE)
    if not token or any(c < "0" or c > "9" for c in token):
        raise SolverError(f"{label}: expected decimal digits")
    # Check lexically before conversion, including arbitrarily many leading zeros.
    significant = token.lstrip("0") or "0"
    if len(significant) > 20 or (len(significant) == 20 and significant > str(MAX_U64)):
        raise SolverError(f"{label}: exceeds uint64 range")
    return int(significant)


def validate(numbers_text: str, target_text: str) -> tuple[list[int], int]:
    tokens = numbers_text.split(",")
    if len(tokens) > MAX_ITEMS:
        raise SolverError("number list exceeds 100000 items", 3)
    numbers: list[int] = []
    seen: set[int] = set()
    for i, token in enumerate(tokens):
        label = f"numbers[{i}]"
        value = parse_integer(token, label)
        if value == 0:
            raise SolverError(f"{label}: must be positive")
        if value in seen:
            raise SolverError(f"{label}: duplicate value")
        seen.add(value)
        numbers.append(value)
    return numbers, parse_integer(target_text, "target")


def lex_less(a: int, b: int) -> bool:
    """Equal-cardinality masks: the first differing index belongs to the winner."""
    diff = a ^ b
    return bool(diff and (a & (diff & -diff)))


def enumerate_subsets(items: list[tuple[int, int]], target: int) -> list[tuple[int, int, int]]:
    records = [(0, 0, 0)]
    for bit, (_, value) in enumerate(items):
        records += [(count + 1, total + value, mask | (1 << bit))
                    for count, total, mask in records if value <= target - total]
    return records


def optimize(numbers: list[int], target: int) -> list[int]:
    eligible = [(i, value) for i, value in enumerate(numbers) if value <= target]
    if sum(value for _, value in eligible) <= target:
        return [i for i, _ in eligible]
    if len(eligible) > 36:
        raise SolverError("exact search requires at most 36 eligible items", 3)
    prefix = 0
    k = 0
    for value in sorted(value for _, value in eligible):
        if value > target - prefix:
            break
        prefix += value
        k += 1
    split = len(eligible) // 2
    left = enumerate_subsets(eligible[:split], target)
    right = enumerate_subsets(eligible[split:], target)
    groups: list[dict[int, int]] = [{} for _ in range(len(eligible) - split + 1)]
    for count, total, mask in right:
        old = groups[count].get(total)
        if old is None or lex_less(mask, old):
            groups[count][total] = mask
    del right
    sums = [sorted(group) for group in groups]
    best_sum = -1
    best_mask = 0
    for count, total, mask in left:
        required = k - count
        if required < 0 or required >= len(groups):
            continue
        position = bisect_right(sums[required], target - total) - 1
        if position < 0:
            continue
        right_sum = sums[required][position]
        combined = mask | (groups[required][right_sum] << split)
        candidate_sum = total + right_sum
        if candidate_sum > best_sum or (candidate_sum == best_sum and lex_less(combined, best_mask)):
            best_sum, best_mask = candidate_sum, combined
    return [original for bit, (original, _) in enumerate(eligible) if best_mask & (1 << bit)]


def format_output(numbers: list[int], target: int, indices: list[int]) -> str:
    selected = [numbers[i] for i in indices]
    total = sum(selected)
    return ("Input Summary\n-------------\n"
            f"Numbers:       {numbers}\nTarget:        {target}\nInput Sum:     {sum(numbers)}\n\n"
            "Optimal Selection\n-----------------\n"
            f"Selected:      {selected}\nItem Count:    {len(selected)}\n"
            f"Selected Sum:  {total}\nDifference:    {target - total}\n")


def run(args: list[str]) -> tuple[int, str, str]:
    try:
        parsed = parse_args(args)
        if parsed is None:
            return 0, HELP, ""
        numbers, target = validate(*parsed)
        indices = optimize(numbers, target)
        return 0, format_output(numbers, target, indices), ""
    except SolverError as error:
        return error.code, "", f"error: {error}\n"
    except MemoryError:
        return 3, "", "error: memory allocation failed\n"


if __name__ == "__main__":
    code, stdout, stderr = run(sys.argv[1:])
    sys.stdout.write(stdout)
    sys.stderr.write(stderr)
    sys.exit(code)
