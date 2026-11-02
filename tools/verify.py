"""Cross-language fixtures and independent exhaustive oracle. Build binaries first."""
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'python'))
import main as python_solver

COMMANDS = {'Go': [str(ROOT/'go/solver')],
            'Python': [sys.executable,str(ROOT/'python/main.py')],
            'Rust': [str(ROOT/'rust/target/release/subset-solver')]}


def expected_output(numbers, target, selected):
    return ('Input Summary\n-------------\n'
            f'Numbers:       {numbers}\nTarget:        {target}\nInput Sum:     {sum(numbers)}\n\n'
            'Optimal Selection\n-----------------\n'
            f'Selected:      {selected}\nItem Count:    {len(selected)}\n'
            f'Selected Sum:  {sum(selected)}\nDifference:    {target-sum(selected)}\n')


def check(name, args, expected):
    for language, command in COMMANDS.items():
        result = subprocess.run(command+args, text=True, capture_output=True, timeout=60)
        actual = result.returncode, result.stdout, result.stderr
        if actual != expected:
            raise AssertionError(f'{name} / {language}:\nactual={actual!r}\nexpected={expected!r}')


def oracle(numbers, target):
    best = ()
    best_sum = 0
    for count in range(len(numbers)+1):
        for indices in itertools.combinations(range(len(numbers)),count):
            total = sum(numbers[i] for i in indices)
            if total <= target and (count > len(best) or count == len(best) and
                                    (total > best_sum or total == best_sum and indices < best)):
                best, best_sum = indices, total
    return [numbers[i] for i in best]


def main():
    fixtures = json.loads((ROOT/'testdata/cases.json').read_text())
    for case in fixtures:
        if 'numbers' in case:
            output = expected_output(list(map(int,case['numbers'])),int(case['target']),list(map(int,case['selected'])))
            expected = (0,output,'')
        elif 'error' in case:
            expected = (case['code'],'','error: '+case['error']+'\n')
        else:
            expected = (0,case['stdout'],'')
        check(case['name'],case['args'],expected)
    rng = random.Random(20261102)
    for i in range(100):
        numbers = rng.sample(range(1,100), rng.randrange(1,14))
        target = rng.randrange(450)
        check(f'oracle_{i}', ['--numbers',','.join(map(str,numbers)),'--target',str(target)],
              (0,expected_output(numbers,target,oracle(numbers,target)),''))
    # Large lists exercise the fast path, filtering, and full-width sums.
    for numbers,target in [(list(range(1,10001)),1000000000), (list(range(1,10001)),1),
                           (list(range(1,37)),666)]:
        selected = [n for n in numbers if n <= target]
        check('large_fast_path',['--numbers',','.join(map(str,numbers)),'--target',str(target)],
              (0,expected_output(numbers,target,selected),''))
    check('reverse_option_order', ['--target','18','--numbers','3,5,7,9'],
          (0,expected_output([3,5,7,9],18,[3,5,9]),''))
    check('36_item_search', ['--numbers',','.join(map(str,range(1,37))),'--target','37'],
          (0,expected_output(list(range(1,37)),37,[1,2,3,4,5,6,7,9]),''))
    # Limits above OS argument limits must be tested through the library entrypoints.
    assert python_solver.run(['--numbers','1,'*100000+'1','--target','1']) == (3,'','error: number list exceeds 100000 items\n')
    assert python_solver.run(['x'*4194305]) == (3,'','error: argument text exceeds 4194304 bytes\n')
    zeros = '0'*5000+'1'
    check('long_leading_zeros',['--numbers',zeros,'--target','1'],(0,expected_output([1],1,[1]),''))
    print(f'PASS: {len(fixtures)} shared fixtures, 100 seeded oracle cases, 6 additional CLI cases across all three languages; Python library limit checks')


if __name__ == '__main__':
    main()
