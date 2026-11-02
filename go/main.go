package main

import (
	"fmt"
	"math/big"
	"os"
	"sort"
	"strconv"
	"strings"
)

const help = "Usage: solver --numbers \"3,5,7,9\" --target 18\n       solver --help\n"
const whitespace = " \t\r\n\f\v"

type solverError struct {
	message string
	code    int
}

func (e *solverError) Error() string { return e.message }
func invalid(message string) error   { return &solverError{message, 2} }
func limited(message string) error   { return &solverError{message, 3} }

func parseArgs(args []string) (string, string, bool, error) {
	size := 0
	for _, arg := range args {
		size += len(arg)
	}
	if size > 4194304 {
		return "", "", false, limited("argument text exceeds 4194304 bytes")
	}
	if len(args) == 1 && args[0] == "--help" {
		return "", "", true, nil
	}
	values := map[string]string{}
	for i := 0; i < len(args); i += 2 {
		flag := args[i]
		if flag != "--numbers" && flag != "--target" {
			return "", "", false, invalid("unknown argument: " + flag)
		}
		if _, exists := values[flag]; exists {
			return "", "", false, invalid("repeated argument: " + flag)
		}
		if i+1 == len(args) || args[i+1] == "--numbers" || args[i+1] == "--target" || args[i+1] == "--help" {
			return "", "", false, invalid("missing value for " + flag)
		}
		values[flag] = args[i+1]
	}
	for _, flag := range []string{"--numbers", "--target"} {
		if _, exists := values[flag]; !exists {
			return "", "", false, invalid("missing required argument: " + flag)
		}
	}
	return values["--numbers"], values["--target"], false, nil
}

func parseInteger(text, label string) (uint64, error) {
	token := strings.Trim(text, whitespace)
	if token == "" {
		return 0, invalid(label + ": expected decimal digits")
	}
	for _, c := range token {
		if c < '0' || c > '9' {
			return 0, invalid(label + ": expected decimal digits")
		}
	}
	token = strings.TrimLeft(token, "0")
	if token == "" {
		return 0, nil
	}
	value, err := strconv.ParseUint(token, 10, 64)
	if err != nil {
		return 0, invalid(label + ": exceeds uint64 range")
	}
	return value, nil
}

func validate(numbersText, targetText string) ([]uint64, uint64, error) {
	tokens := strings.Split(numbersText, ",")
	if len(tokens) > 100000 {
		return nil, 0, limited("number list exceeds 100000 items")
	}
	numbers := make([]uint64, 0, len(tokens))
	seen := map[uint64]bool{}
	for i, token := range tokens {
		label := fmt.Sprintf("numbers[%d]", i)
		value, err := parseInteger(token, label)
		if err != nil {
			return nil, 0, err
		}
		if value == 0 {
			return nil, 0, invalid(label + ": must be positive")
		}
		if seen[value] {
			return nil, 0, invalid(label + ": duplicate value")
		}
		seen[value] = true
		numbers = append(numbers, value)
	}
	target, err := parseInteger(targetText, "target")
	return numbers, target, err
}

type item struct {
	index int
	value uint64
}
type record struct {
	count     int
	sum, mask uint64
}

func lexLess(a, b uint64) bool { diff := a ^ b; return diff != 0 && a&(diff&-diff) != 0 }
func enumerateSubsets(items []item, target uint64) []record {
	records := []record{{}}
	for bit, item := range items {
		length := len(records)
		for j := 0; j < length; j++ {
			r := records[j]
			if item.value <= target-r.sum {
				records = append(records, record{r.count + 1, r.sum + item.value, r.mask | (uint64(1) << bit)})
			}
		}
	}
	return records
}
func optimize(numbers []uint64, target uint64) ([]int, error) {
	eligible := []item{}
	total := uint64(0)
	allFit := true
	for i, value := range numbers {
		if value <= target {
			eligible = append(eligible, item{i, value})
			if allFit {
				if value > target-total {
					allFit = false
				} else {
					total += value
				}
			}
		}
	}
	if allFit {
		result := []int{}
		for _, item := range eligible {
			result = append(result, item.index)
		}
		return result, nil
	}
	if len(eligible) > 36 {
		return nil, limited("exact search requires at most 36 eligible items")
	}
	values := make([]uint64, len(eligible))
	for i, item := range eligible {
		values[i] = item.value
	}
	sort.Slice(values, func(i, j int) bool { return values[i] < values[j] })
	prefix := uint64(0)
	k := 0
	for _, value := range values {
		if value > target-prefix {
			break
		}
		prefix += value
		k++
	}
	split := len(eligible) / 2
	left := enumerateSubsets(eligible[:split], target)
	right := enumerateSubsets(eligible[split:], target)
	groups := make([][]record, len(eligible)-split+1)
	for _, r := range right {
		groups[r.count] = append(groups[r.count], r)
	}
	for i, group := range groups {
		sort.Slice(group, func(a, b int) bool {
			if group[a].sum != group[b].sum {
				return group[a].sum < group[b].sum
			}
			return lexLess(group[a].mask, group[b].mask)
		})
		compact := group[:0]
		for _, r := range group {
			if len(compact) == 0 || compact[len(compact)-1].sum != r.sum {
				compact = append(compact, r)
			}
		}
		groups[i] = compact
	}
	bestSum, bestMask := uint64(0), uint64(0)
	found := false
	for _, l := range left {
		required := k - l.count
		if required < 0 || required >= len(groups) {
			continue
		}
		group := groups[required]
		pos := sort.Search(len(group), func(i int) bool { return group[i].sum > target-l.sum }) - 1
		if pos < 0 {
			continue
		}
		r := group[pos]
		sum := l.sum + r.sum
		mask := l.mask | (r.mask << split)
		if !found || sum > bestSum || sum == bestSum && lexLess(mask, bestMask) {
			bestSum, bestMask, found = sum, mask, true
		}
	}
	result := []int{}
	for bit, item := range eligible {
		if bestMask&(uint64(1)<<bit) != 0 {
			result = append(result, item.index)
		}
	}
	return result, nil
}
func listText(values []uint64) string {
	parts := make([]string, len(values))
	for i, value := range values {
		parts[i] = strconv.FormatUint(value, 10)
	}
	return "[" + strings.Join(parts, ", ") + "]"
}
func formatOutput(numbers []uint64, target uint64, indices []int) string {
	inputSum := new(big.Int)
	for _, value := range numbers {
		inputSum.Add(inputSum, new(big.Int).SetUint64(value))
	}
	selected := []uint64{}
	sum := uint64(0)
	for _, i := range indices {
		selected = append(selected, numbers[i])
		sum += numbers[i]
	}
	return fmt.Sprintf("Input Summary\n-------------\nNumbers:       %s\nTarget:        %d\nInput Sum:     %s\n\nOptimal Selection\n-----------------\nSelected:      %s\nItem Count:    %d\nSelected Sum:  %d\nDifference:    %d\n", listText(numbers), target, inputSum.String(), listText(selected), len(selected), sum, target-sum)
}
func run(args []string) (int, string, string) {
	numbersText, targetText, wantsHelp, err := parseArgs(args)
	if err == nil && wantsHelp {
		return 0, help, ""
	}
	var numbers []uint64
	var target uint64
	var indices []int
	if err == nil {
		numbers, target, err = validate(numbersText, targetText)
	}
	if err == nil {
		indices, err = optimize(numbers, target)
	}
	if err != nil {
		e := err.(*solverError)
		return e.code, "", "error: " + e.message + "\n"
	}
	return 0, formatOutput(numbers, target, indices), ""
}
func main() {
	code, out, err := run(os.Args[1:])
	fmt.Print(out)
	fmt.Fprint(os.Stderr, err)
	os.Exit(code)
}
