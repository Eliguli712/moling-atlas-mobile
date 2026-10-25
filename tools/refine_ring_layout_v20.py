from pathlib import Path
import json,math,copy
import numpy as np
from revise_atlas_v20 import RingPlanner,decode,encode,dumps,xy,delta
R=Path(__file__).resolve().parent.parent;OUT=R/'dist';files={};A={}
for p in sorted((OUT/'data').glob('*a*.js')):
    o=json.loads(p.read_text().split('=',1)[1].rstrip(';'));files[p]=o;A.update(o)
baseline={}
for p in (R.parent/'atlas-v19/data').glob('*a*.js'):baseline.update(json.loads(p.read_text().split('=',1)[1].rstrip(';')))
report={};changed={}
for k,v in A.items():
    if not k.startswith('c/'):continue
    c=decode(v)
    if not c.get('ring_revision_v20'):continue
    old=decode(baseline[k])
    for field in ['mn','ml','lrt']:c[field]=copy.deepcopy(old[field])
    print('Refining',c['k'],flush=True);report[c['k']]=RingPlanner(c).revise();changed[k]=c
def put(k,v):
    for o in files.values():
        if k in o:o[k]=encode(v);return
for k,c in changed.items():put(k,c)
C=decode(A['l_city.json']);D=decode(json.loads((OUT/'data/v20_d.js').read_text().split('=',1)[1].rstrip(';')));P=D['proj']
def ll(c,a):
    x=(c['o'][0]+a[...,0])*1000;y=(c['o'][1]-a[...,1])*1000;e=math.sqrt(P['E2']);rho=np.hypot(x,P['RHO0']-y);th=np.arctan2(x,P['RHO0']-y);q=P['QP']*(P['C']-(rho*P['N']/P['RA'])**2)/(2*P['N']);lat=np.arcsin(np.clip(q/P['QP'],-1,1))
    for _ in range(8):
        ss=np.sin(lat);v=(1-P['E2'])*(ss/(1-P['E2']*ss*ss)-np.log((1-e*ss)/(1+e*ss))/(2*e));lat+=(q-v)/(2*(1-P['E2'])*np.cos(lat)/(1-P['E2']*ss*ss)**2)
    return np.stack([(th/P['N']+P['L0'])*180/np.pi,lat*180/np.pi],axis=-1)
for s in C['city']:
    c=changed.get('c/'+s['k']+'.json')
    if not c:continue
    s['ml']=[dict(n=l['n'],col=l['col'],s={'运营':'运','在建':'建','规划':'规'}.get(l['s'],l['s']),q=delta(ll(c,xy(l['q'])),10000)) for l in c['ml']]
    for n,raw in zip(s['ms'],c['mn']):n['c']=np.round(ll(c,np.array(raw['c'])/20),6).tolist()
put('l_city.json',C)
for p,o in files.items():p.write_text(p.read_text().split('=',1)[0]+'='+dumps(o)+';')
(OUT/'ring-layout-v20.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('Refined',len(report),'cities')
