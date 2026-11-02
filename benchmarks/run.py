"""Repeated CLI, startup, core timing, and GNU time RSS measurements."""
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'python'))
sys.path.insert(0,str(ROOT/'tools'))
import main as solver
from verify import COMMANDS, expected_output, oracle


def execute(command, **kwargs):
    return subprocess.run(command,check=True,capture_output=True,text=True,**kwargs)


def sample(command, expected, count=5):
    samples=[]
    for _ in range(count):
        start=time.perf_counter()
        result=execute(command)
        samples.append(time.perf_counter()-start)
        assert result.stdout==expected and not result.stderr
    return samples


def stats(samples):
    return {'median_seconds':statistics.median(samples),'min_seconds':min(samples),
            'max_seconds':max(samples),'samples_seconds':samples}


def main():
    manifest=json.loads((ROOT/'benchmarks/workloads.json').read_text())
    results={'environment':{'platform':platform.platform(),'python':sys.version,
             'cpu':next((line.split(':',1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name')), 'unknown'),
             'go':execute(['go','version']).stdout.strip(),
             'rust':execute(['rustc','--version']).stdout.strip(),
             'logical_cpus':os.cpu_count()},'seed':manifest['seed'],'startup':{},'workloads':[]}
    for language,command in COMMANDS.items():
        results['startup'][language]=stats(sample(command+['--help'],solver.HELP,10))
    for workload in manifest['workloads']:
        path=ROOT/'benchmarks'/workload['file']
        numbers_text,target_text=path.read_text().splitlines()
        numbers,target=solver.validate(numbers_text,target_text)
        indices=solver.optimize(numbers,target)
        selected=[numbers[i] for i in indices]
        if len(numbers)<=24:
            assert selected==oracle(numbers,target)
        # At larger sizes CLI agreement checks independent implementations.
        expected=expected_output(numbers,target,selected)
        entry={**workload,'selected_count':len(selected),'selected_sum':str(sum(selected)),'languages':{}}
        for language,command in COMMANDS.items():
            args=command+['--numbers',numbers_text,'--target',target_text]
            execute(args)  # warm up file caches
            measurements={'cli':stats(sample(args,expected))}
            if Path('/usr/bin/time').exists():
                with tempfile.TemporaryDirectory() as tmp:
                    report=Path(tmp)/'rss.txt'
                    result=execute(['/usr/bin/time','-f','%M','-o',str(report)]+args)
                    assert result.stdout==expected and not result.stderr
                    measurements['peak_rss_kib']=int(report.read_text().strip())
            samples=[]
            iterations=workload['core_iterations']
            for _ in range(3):
                if language=='Python':
                    start=time.perf_counter()
                    for _ in range(iterations):
                        actual=solver.optimize(numbers,target)
                    samples.append((time.perf_counter()-start)/iterations)
                    assert actual==indices
                else:
                    if language=='Go':
                        result=execute([str(ROOT/'benchmarks/bin/go-core'),'-test.run=^TestCoreTiming$','-test.v'],
                                       env={**os.environ,'SUBSET_WORKLOAD':str(path),'SUBSET_ITERATIONS':str(iterations)})
                    else:
                        result=execute([str(ROOT/'rust/target/release/examples/core'),str(path),str(iterations)])
                    line=next(line for line in result.stdout.splitlines() if line.startswith('CORE '))
                    _,seconds,count,total=line.split()
                    assert (int(count),int(total))==(len(selected),sum(selected))
                    samples.append(float(seconds))
            measurements['core']=stats(samples)
            entry['languages'][language]=measurements
        results['workloads'].append(entry)
        print(f"Measured {workload['name']}",flush=True)
    (ROOT/'benchmarks/results.json').write_text(json.dumps(results,indent=2)+'\n')
    print('Saved benchmarks/results.json')


if __name__=='__main__':
    main()
