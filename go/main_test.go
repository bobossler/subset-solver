package main

import (
	"reflect"
	"testing"
)

func TestObjectives(t *testing.T) {
	cases := []struct {
		numbers []uint64
		target  uint64
		want    []int
	}{
		{[]uint64{3, 5, 7, 9}, 18, []int{0, 1, 3}},
		{[]uint64{2, 3, 9}, 9, []int{0, 1}},
		{[]uint64{4, 1, 3, 2}, 5, []int{0, 1}},
		{[]uint64{1, 2}, 0, []int{}},
	}
	for _, c := range cases {
		got, err := optimize(c.numbers, c.target)
		if err != nil || !reflect.DeepEqual(got, c.want) {
			t.Fatalf("got %v, %v; want %v", got, err, c.want)
		}
	}
}
func TestValidation(t *testing.T) {
	for _, numbers := range []string{"3,03", "0", "-1", "3,,4"} {
		if _, _, err := validate(numbers, "4"); err == nil {
			t.Fatalf("accepted %s", numbers)
		}
	}
	if _, _, err := validate("1", "18446744073709551616"); err == nil {
		t.Fatal("accepted overflow")
	}
	numbers, target, err := validate(" 03,\t5 ", " 8 ")
	if err != nil || target != 8 || !reflect.DeepEqual(numbers, []uint64{3, 5}) {
		t.Fatal(numbers, target, err)
	}
}
func indicesLess(a, b []int) bool {
	for i := range a {
		if a[i] != b[i] {
			return a[i] < b[i]
		}
	}
	return false
}
func TestBruteForce(t *testing.T) {
	for seed := 0; seed < 60; seed++ {
		numbers := make([]uint64, 10)
		for i := range numbers {
			numbers[i] = uint64((i*17+seed*13)%41 + 1)
		}
		if seed%2 == 0 {
			for i, j := 0, len(numbers)-1; i < j; i, j = i+1, j-1 {
				numbers[i], numbers[j] = numbers[j], numbers[i]
			}
		}
		target := uint64(seed * 7 % 180)
		best := []int{}
		bestSum := uint64(0)
		for mask := 0; mask < 1<<len(numbers); mask++ {
			candidate := []int{}
			sum := uint64(0)
			for i, v := range numbers {
				if mask&(1<<i) != 0 {
					candidate = append(candidate, i)
					sum += v
				}
			}
			if sum <= target && (len(candidate) > len(best) || len(candidate) == len(best) && (sum > bestSum || sum == bestSum && indicesLess(candidate, best))) {
				best, bestSum = candidate, sum
			}
		}
		got, err := optimize(numbers, target)
		if err != nil || !reflect.DeepEqual(got, best) {
			t.Fatalf("seed %d: got %v %v want %v", seed, got, err, best)
		}
	}
}
