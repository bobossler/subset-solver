import itertools
import random
import unittest
from main import optimize, parse_integer, run, validate


class SolverTests(unittest.TestCase):
    def test_objectives(self):
        self.assertEqual(optimize([3, 5, 7, 9], 18), [0, 1, 3])
        self.assertEqual(optimize([2, 3, 9], 9), [0, 1])
        self.assertEqual(optimize([4, 1, 3, 2], 5), [0, 1])
        self.assertEqual(optimize([1, 2], 0), [])

    def test_validation(self):
        for numbers in ('3,03', '0', '-1', '3,,4'):
            self.assertEqual(run(['--numbers', numbers, '--target', '4'])[0], 2)
        self.assertEqual(validate(' 03,\t5 ', ' 8 '), ([3, 5], 8))
        self.assertEqual(parse_integer('0' * 5000 + '1', 'value'), 1)
        self.assertEqual(run(['--numbers', '1', '--target', str(1 << 64)])[0], 2)

    def test_brute_force(self):
        rng = random.Random(20261102)
        for _ in range(120):
            numbers = rng.sample(range(1, 100), rng.randrange(1, 13))
            target = rng.randrange(400)
            feasible = (indices for size in range(len(numbers) + 1)
                        for indices in itertools.combinations(range(len(numbers)), size)
                        if sum(numbers[i] for i in indices) <= target)
            best = min(feasible, key=lambda indices: (-len(indices), -sum(numbers[i] for i in indices), indices))
            self.assertEqual(optimize(numbers, target), list(best))


if __name__ == '__main__':
    unittest.main()
