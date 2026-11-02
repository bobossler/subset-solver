"""Create deterministic saved benchmark inputs. Run from any directory."""
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parent
rng = random.Random(20261102)
workloads = []

def add(name, numbers, target, iterations):
    filename = name+'.txt'
    (ROOT/'data'/filename).write_text(','.join(map(str,numbers))+'\n'+str(target)+'\n')
    workloads.append({'name':name,'file':'data/'+filename,'n':len(numbers),'target':str(target),'core_iterations':iterations})


(ROOT/'data').mkdir(exist_ok=True)
a = rng.sample(range(1,100),12)
add('small',a,sum(a)//2,50)
a = rng.sample(range(1,10001),24)
add('medium',a,sum(a)//2,5)
a = rng.sample(range(1,1000001),36)
add('large_search',a,sum(a)*3//5,2)
a = rng.sample(range(10**17,10**17+10**9),30)
add('large_values',a,sum(a)//2,3)
a = rng.sample(range(1,1000001),36)
add('few_fit',a,sorted(a)[3],30)
a = rng.sample(range(1,1000001),30)
add('most_fit',a,sum(a)-min(a),2)
a = rng.sample(range(1,1000000),10000)
add('large_list_all_fit',a,sum(a),20)
a = rng.sample(range(1000,1000000),10000)
add('large_list_small_target',a,10,30)
(ROOT/'workloads.json').write_text(json.dumps({'seed':20261102,'workloads':workloads},indent=2)+'\n')
print(f'Wrote {len(workloads)} workloads')
