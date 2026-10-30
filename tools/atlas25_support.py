"""Read the immutable v24 baseline for the v25 release."""
from pathlib import Path
import json,pickle
from revise_atlas_v20 import decode,encode,dumps,xy,delta,pack,area
R=Path(__file__).resolve().parents[1];O=R/'dist';T=R/'analysis-v25';T.mkdir(exist_ok=True)
def baseline25():
 p=T/'base-v24.pkl'
 if p.exists():return pickle.load(p.open('rb'))
 D=decode(json.loads((O/'data/v24_d.js').read_text().split('=',1)[1].strip().rstrip(';')));A={};F={}
 for f in sorted((O/'data').glob('v24*.js')):
  if f.name in ['v24_d.js','v24_rasters.js']:continue
  prefix,body=f.read_text().split('=',1);data=json.loads(body.strip().rstrip(';'));F[f.name]=(prefix,data);A.update(data)
 C=decode(A['l_city.json']);out=(D,A,F,C);pickle.dump(out,p.open('wb'));return out
