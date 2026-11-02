use std::collections::HashSet;

pub const HELP: &str = "Usage: solver --numbers \"3,5,7,9\" --target 18\n       solver --help\n";
const WHITESPACE: &[char] = &[' ', '\t', '\r', '\n', '\x0c', '\x0b'];
#[derive(Debug)]
pub struct SolverError {
    pub message: String,
    pub code: i32,
}
fn invalid(message: impl Into<String>) -> SolverError {
    SolverError {
        message: message.into(),
        code: 2,
    }
}
fn limited(message: &str) -> SolverError {
    SolverError {
        message: message.into(),
        code: 3,
    }
}

pub fn parse_args(args: &[String]) -> Result<Option<(&str, &str)>, SolverError> {
    if args.iter().map(|s| s.len()).sum::<usize>() > 4194304 {
        return Err(limited("argument text exceeds 4194304 bytes"));
    }
    if args.len() == 1 && args[0] == "--help" {
        return Ok(None);
    }
    let mut numbers = None;
    let mut target = None;
    let mut i = 0;
    while i < args.len() {
        let flag = args[i].as_str();
        let slot = match flag {
            "--numbers" => &mut numbers,
            "--target" => &mut target,
            _ => return Err(invalid(format!("unknown argument: {flag}"))),
        };
        if slot.is_some() {
            return Err(invalid(format!("repeated argument: {flag}")));
        }
        if i + 1 == args.len()
            || matches!(args[i + 1].as_str(), "--numbers" | "--target" | "--help")
        {
            return Err(invalid(format!("missing value for {flag}")));
        }
        *slot = Some(args[i + 1].as_str());
        i += 2;
    }
    let numbers = numbers.ok_or_else(|| invalid("missing required argument: --numbers"))?;
    let target = target.ok_or_else(|| invalid("missing required argument: --target"))?;
    Ok(Some((numbers, target)))
}

pub fn parse_integer(text: &str, label: &str) -> Result<u64, SolverError> {
    let token = text.trim_matches(WHITESPACE);
    if token.is_empty() || !token.bytes().all(|b| b.is_ascii_digit()) {
        return Err(invalid(format!("{label}: expected decimal digits")));
    }
    let token = token.trim_start_matches('0');
    if token.is_empty() {
        return Ok(0);
    }
    token
        .parse()
        .map_err(|_| invalid(format!("{label}: exceeds uint64 range")))
}
pub fn validate(numbers_text: &str, target_text: &str) -> Result<(Vec<u64>, u64), SolverError> {
    let tokens: Vec<_> = numbers_text.split(',').collect();
    if tokens.len() > 100000 {
        return Err(limited("number list exceeds 100000 items"));
    }
    let mut numbers = Vec::with_capacity(tokens.len());
    let mut seen = HashSet::new();
    for (i, token) in tokens.iter().enumerate() {
        let label = format!("numbers[{i}]");
        let value = parse_integer(token, &label)?;
        if value == 0 {
            return Err(invalid(format!("{label}: must be positive")));
        }
        if !seen.insert(value) {
            return Err(invalid(format!("{label}: duplicate value")));
        }
        numbers.push(value);
    }
    Ok((numbers, parse_integer(target_text, "target")?))
}

#[derive(Clone, Copy)]
struct Record {
    count: usize,
    sum: u64,
    mask: u64,
}
fn lex_less(a: u64, b: u64) -> bool {
    let diff = a ^ b;
    diff != 0 && a & (diff & diff.wrapping_neg()) != 0
}
fn enumerate_subsets(items: &[(usize, u64)], target: u64) -> Vec<Record> {
    let mut records = vec![Record {
        count: 0,
        sum: 0,
        mask: 0,
    }];
    for (bit, &(_, value)) in items.iter().enumerate() {
        let length = records.len();
        for j in 0..length {
            let r = records[j];
            if value <= target - r.sum {
                records.push(Record {
                    count: r.count + 1,
                    sum: r.sum + value,
                    mask: r.mask | (1 << bit),
                });
            }
        }
    }
    records
}
pub fn optimize(numbers: &[u64], target: u64) -> Result<Vec<usize>, SolverError> {
    let eligible: Vec<_> = numbers
        .iter()
        .copied()
        .enumerate()
        .filter(|&(_, v)| v <= target)
        .collect();
    if eligible.iter().map(|&(_, v)| u128::from(v)).sum::<u128>() <= u128::from(target) {
        return Ok(eligible.iter().map(|&(i, _)| i).collect());
    }
    if eligible.len() > 36 {
        return Err(limited("exact search requires at most 36 eligible items"));
    }
    let mut values: Vec<_> = eligible.iter().map(|&(_, v)| v).collect();
    values.sort_unstable();
    let mut prefix = 0;
    let mut k = 0;
    for value in values {
        if value > target - prefix {
            break;
        }
        prefix += value;
        k += 1;
    }
    let split = eligible.len() / 2;
    let left = enumerate_subsets(&eligible[..split], target);
    let right = enumerate_subsets(&eligible[split..], target);
    let mut groups = vec![Vec::new(); eligible.len() - split + 1];
    for r in right {
        groups[r.count].push(r);
    }
    for group in &mut groups {
        group.sort_unstable_by(|a, b| {
            a.sum.cmp(&b.sum).then_with(|| {
                if a.mask == b.mask {
                    std::cmp::Ordering::Equal
                } else if lex_less(a.mask, b.mask) {
                    std::cmp::Ordering::Less
                } else {
                    std::cmp::Ordering::Greater
                }
            })
        });
        group.dedup_by_key(|r| r.sum);
    }
    let mut best: Option<(u64, u64)> = None;
    for l in left {
        if l.count > k || k - l.count >= groups.len() {
            continue;
        }
        let group = &groups[k - l.count];
        let pos = group.partition_point(|r| r.sum <= target - l.sum);
        if pos == 0 {
            continue;
        }
        let r = group[pos - 1];
        let sum = l.sum + r.sum;
        let mask = l.mask | (r.mask << split);
        if best.map_or(true, |(old_sum, old_mask)| {
            sum > old_sum || (sum == old_sum && lex_less(mask, old_mask))
        }) {
            best = Some((sum, mask));
        }
    }
    let mask = best.expect("maximum feasible count has a candidate").1;
    Ok(eligible
        .iter()
        .enumerate()
        .filter_map(|(bit, &(i, _))| {
            if mask & (1 << bit) != 0 {
                Some(i)
            } else {
                None
            }
        })
        .collect())
}
fn list_text(values: &[u64]) -> String {
    format!(
        "[{}]",
        values
            .iter()
            .map(u64::to_string)
            .collect::<Vec<_>>()
            .join(", ")
    )
}
pub fn format_output(numbers: &[u64], target: u64, indices: &[usize]) -> String {
    let input_sum: u128 = numbers.iter().map(|&v| u128::from(v)).sum();
    let selected: Vec<_> = indices.iter().map(|&i| numbers[i]).collect();
    let sum: u64 = selected.iter().sum();
    format!("Input Summary\n-------------\nNumbers:       {}\nTarget:        {}\nInput Sum:     {}\n\nOptimal Selection\n-----------------\nSelected:      {}\nItem Count:    {}\nSelected Sum:  {}\nDifference:    {}\n", list_text(numbers), target, input_sum, list_text(&selected), selected.len(), sum, target-sum)
}
pub fn run(args: &[String]) -> (i32, String, String) {
    let result = (|| {
        let Some((numbers_text, target_text)) = parse_args(args)? else {
            return Ok(HELP.to_string());
        };
        let (numbers, target) = validate(numbers_text, target_text)?;
        let indices = optimize(&numbers, target)?;
        Ok::<_, SolverError>(format_output(&numbers, target, &indices))
    })();
    match result {
        Ok(out) => (0, out, String::new()),
        Err(error) => (
            error.code,
            String::new(),
            format!("error: {}\n", error.message),
        ),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn objectives() {
        assert_eq!(optimize(&[3, 5, 7, 9], 18).unwrap(), vec![0, 1, 3]);
        assert_eq!(optimize(&[2, 3, 9], 9).unwrap(), vec![0, 1]);
        assert_eq!(optimize(&[4, 1, 3, 2], 5).unwrap(), vec![0, 1]);
        assert_eq!(optimize(&[1, 2], 0).unwrap(), Vec::<usize>::new());
    }
    #[test]
    fn validation() {
        assert!(validate("3,03", "4").is_err());
        assert!(validate("0", "4").is_err());
        assert!(validate("1", "18446744073709551616").is_err());
        assert_eq!(validate(" 03,\t5 ", " 8 ").unwrap(), (vec![3, 5], 8));
        assert_eq!(
            parse_integer(&format!("{}1", "0".repeat(5000)), "value").unwrap(),
            1
        );
    }
    #[test]
    fn brute_force() {
        for seed in 0..60u64 {
            let mut numbers: Vec<_> = (0..10).map(|i| (i * 17 + seed * 13) % 41 + 1).collect();
            if seed % 2 == 0 {
                numbers.reverse();
            }
            let target = seed * 7 % 180;
            let mut best: Vec<usize> = Vec::new();
            let mut best_sum = 0;
            for mask in 0..1usize << numbers.len() {
                let candidate: Vec<_> = (0..numbers.len())
                    .filter(|&i| mask & (1 << i) != 0)
                    .collect();
                let sum: u64 = candidate.iter().map(|&i| numbers[i]).sum();
                if sum <= target
                    && (candidate.len() > best.len()
                        || candidate.len() == best.len()
                            && (sum > best_sum || sum == best_sum && candidate < best))
                {
                    best = candidate;
                    best_sum = sum;
                }
            }
            assert_eq!(optimize(&numbers, target).unwrap(), best);
        }
    }
}

#[cfg(test)]
mod resource_tests {
    use super::*;
    #[test]
    fn limits() {
        assert_eq!(run(&["x".repeat(4194305)]).0, 3);
        assert_eq!(
            run(&[
                "--numbers".into(),
                format!("{}1", "1,".repeat(100000)),
                "--target".into(),
                "1".into()
            ])
            .0,
            3
        );
    }
}
