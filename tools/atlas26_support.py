"""Immutable v25 release input for the focused v26 frontier correction."""
from atlas25_support import R,O,decode,encode,dumps,xy,delta,area
from atlas24_support import generated_at,planning_namespace
from pathlib import Path
import json,pickle
T=R/'analysis-v26';T.mkdir(exist_ok=True)
BASE='f28c1cfb6bb5d13c67c09b5d13e533f9851c0c6b'
def baseline26():
 p=T/'base-v25.pkl'
 if p.exists():return pickle.load(p.open('rb'))
 D=decode(json.loads(generated_at(BASE,'dist/data/v25_d.js').decode().split('=',1)[1].strip().rstrip(';')));A={};F={}
 for name in [*[f'v25_a4_{i}.js' for i in range(5)],*[f'v25_a5_{i}.js' for i in range(4)],'v25_extra.js']:
  prefix,body=generated_at(BASE,'dist/data/'+name).decode().split('=',1);data=json.loads(body.strip().rstrip(';'));F[name]=(prefix,data);A.update(data)
 C=decode(A['l_city.json']);result=(D,A,F,C);pickle.dump(result,p.open('wb'));return result
