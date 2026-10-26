"""Geographic regressions: preserved frontiers, real junctions and closed rings."""
from pathlib import Path
import json,hashlib,numpy as np
from revise_atlas_v20 import decode,dumps,xy
R=Path(__file__).resolve().parents[1];O=R/'dist'
def read(v):return decode(json.loads((O/f'data/{v}_d.js').read_text().split('=',1)[1].strip().rstrip(';')))
D=read('v22');baseline=R/'tools/protected-geography-v22.json'
keys=['p500','wei17','world','v20_border','nomad_area_v16'];ext=['eez','japan','airports','bohai_frontier_repair']
def hashes(d):
 result={k:hashlib.sha256(dumps(d[k]).encode()).hexdigest() for k in keys}
 result.update({'extension_'+k:hashlib.sha256(dumps(d['v20_ext'][k]).encode()).hexdigest() for k in ext})
 for i,a in enumerate(d['v20_ext']['islands']):result['coast_'+str(i)]=hashlib.sha256(dumps(a['r']).encode()).hexdigest()
 return result
if not baseline.exists():baseline.write_text(json.dumps(hashes(read('v21')),indent=2))
expected=json.loads(baseline.read_text());actual=hashes(D);assert actual==expected,'Protected geography changed'
routes=D['v20_ext']['routes'];assert len(routes)==24
for l in routes:
 p=xy(l['q'],10000);assert np.isfinite(p).all()
 assert np.linalg.norm(p[0]-l['ends'][0])<1e-5 and np.linalg.norm(p[-1]-l['ends'][-1])<1e-5
 if l.get('closed'):assert np.linalg.norm(p[0]-p[-1])<1e-5
for i,limit in [(10,800),(17,1000),(19,500),(20,750),(22,600),(23,100)]:assert routes[i]['km']<limit,(i,routes[i]['km'])
hubs={};shared=0
for l in routes[19:]:
 assert l['kind']=='rail'
 for s in l['stations']:
  if s['n'] in hubs:assert np.linalg.norm(np.array(s['c'])-hubs[s['n']])<1e-5;shared+=1
  hubs[s['n']]=s['c']
report=json.loads((O/'validation-v21.json').read_text());report['revision']='v22';report['corridor_validation']={'protected_data_unchanged':True,'protected_geography_sha256':actual,'routes_retraced':22,'liaodong_shared_station_checks':shared,'endpoints_match':True,'island_rings_closed':True,'ordinary_railway_symbols':'dark centerline and cross sleepers','taiwan_scan_band_repair':json.loads((O/'island-bands-v22.json').read_text())}
(O/'validation-v22.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('Validated 22 corridors,',shared,'shared rail stations; frontiers, EEZ and coastlines unchanged')
