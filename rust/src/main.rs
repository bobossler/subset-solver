fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let (code, out, err) = subset_solver::run(&args);
    print!("{out}");
    eprint!("{err}");
    std::process::exit(code);
}
