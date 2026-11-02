use std::{env, fs, time::Instant};
use subset_solver::{optimize, validate};
fn main() {
    let args: Vec<_> = env::args().collect();
    let data = fs::read_to_string(&args[1]).unwrap();
    let mut lines = data.lines();
    let (numbers, target) = validate(lines.next().unwrap(), lines.next().unwrap()).unwrap();
    let iterations: usize = args[2].parse().unwrap();
    assert!(iterations > 0);
    let mut selected = Vec::new();
    let start = Instant::now();
    for _ in 0..iterations {
        selected = optimize(std::hint::black_box(&numbers), std::hint::black_box(target)).unwrap();
        std::hint::black_box(&selected);
    }
    let elapsed = start.elapsed().as_secs_f64() / iterations as f64;
    let sum: u64 = selected.iter().map(|&i| numbers[i]).sum();
    println!("CORE {:.12} {} {}", elapsed, selected.len(), sum);
}
