package main

import (
	"fmt"
	"os"
	"strconv"
	"strings"
	"testing"
	"time"
)

// This test is an opt-in core timing driver, compiled with go test -c.
func TestCoreTiming(t *testing.T) {
	path := os.Getenv("SUBSET_WORKLOAD")
	if path == "" {
		t.Skip("benchmark driver only")
	}
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	lines := strings.Split(strings.TrimSpace(string(data)), "\n")
	numbers, target, err := validate(lines[0], lines[1])
	if err != nil {
		t.Fatal(err)
	}
	iterations, err := strconv.Atoi(os.Getenv("SUBSET_ITERATIONS"))
	if err != nil || iterations < 1 {
		t.Fatal("invalid iteration count")
	}
	var selected []int
	start := time.Now()
	for i := 0; i < iterations; i++ {
		selected, err = optimize(numbers, target)
		if err != nil {
			t.Fatal(err)
		}
	}
	elapsed := time.Since(start).Seconds() / float64(iterations)
	sum := uint64(0)
	for _, index := range selected {
		sum += numbers[index]
	}
	fmt.Printf("CORE %.12f %d %d\n", elapsed, len(selected), sum)
}

func TestResourceLimits(t *testing.T) {
	code, _, _ := run([]string{strings.Repeat("x", 4194305)})
	if code != 3 {
		t.Fatal("byte limit")
	}
	code, _, _ = run([]string{"--numbers", strings.Repeat("1,", 100000) + "1", "--target", "1"})
	if code != 3 {
		t.Fatal("item limit")
	}
	value, err := parseInteger(strings.Repeat("0", 5000)+"1", "value")
	if err != nil || value != 1 {
		t.Fatal(value, err)
	}
}
