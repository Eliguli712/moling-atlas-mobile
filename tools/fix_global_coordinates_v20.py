"""Honor each city's retained local projection when updating world overlays."""
from pathlib import Path
import json,math
import numpy as np
from revise_atlas_v20 import decode,encode,dumps,xy,delta
R=Path(__file__).resolve().parent.parent;O=R/'dist';files={};A={}
for p in sorted((O/'data').glob('*a*.js')):
    obj=json.loads(p.read_text().split('=',1)[1].rstrip(';'));files[p]=obj;A.update(obj)
C=decode(A['l_city.json']);D=decode(json.loads((O/'data/v20_d.js').read_text().split('=',1)[1].rstrip(';')));P=D['proj']
def ll(c,p):
    p=np.asarray(p);x=c['o'][0]+p[...,0];y=c['o'][1]-p[...,1];t=c.get('lt')
    if t and t.get('kind')=='aeqd':
        lon0=math.radians(t['lon0']);lat0=math.radians(t['lat0']);rho=np.hypot(x,y);angle=rho/(t['R']/1000);r=np.maximum(rho,1e-12)
        lat=np.arcsin(np.clip(np.cos(angle)*math.sin(lat0)+y*np.sin(angle)*math.cos(lat0)/r,-1,1))
        lon=lon0+np.arctan2(x*np.sin(angle),rho*math.cos(lat0)*np.cos(angle)-y*math.sin(lat0)*np.sin(angle))
        return np.stack([np.degrees(lon),np.degrees(lat)],axis=-1)
    x=x*1000;y=y*1000;e=math.sqrt(P['E2']);rho=np.hypot(x,P['RHO0']-y);th=np.arctan2(x,P['RHO0']-y);q=P['QP']*(P['C']-(rho*P['N']/P['RA'])**2)/(2*P['N']);lat=np.arcsin(np.clip(q/P['QP'],-1,1))
    for _ in range(8):
        ss=np.sin(lat);v=(1-P['E2'])*(ss/(1-P['E2']*ss*ss)-np.log((1-e*ss)/(1+e*ss))/(2*e));lat+=(q-v)/(2*(1-P['E2'])*np.cos(lat)/(1-P['E2']*ss*ss)**2)
    return np.stack([(th/P['N']+P['L0'])*180/np.pi,lat*180/np.pi],axis=-1)
raws={};audit=[]
for s in C['city']:
    c=decode(A['c/'+s['k']+'.json']);raws[s['k']]=c
    if not c.get('ring_revision_v20'):continue
    s['ml']=[dict(n=l['n'],col=l['col'],s={'运营':'运','在建':'建','规划':'规'}.get(l['s'],l['s']),q=delta(ll(c,xy(l['q'])),10000)) for l in c['ml']]
    for n,raw in zip(s['ms'],c['mn']):n['c']=np.round(ll(c,np.array(raw['c'])/20),6).tolist()
    # A metro map's world footprint must stay close to its own city centre.
    points=np.vstack([xy(l['q'],10000) for l in s['ml']]);mid=np.median(points,axis=0)
    err=np.linalg.norm((mid-[s['lon'],s['lat']])*[math.cos(math.radians(s['lat'])),1])*111
    if err>c['w']*1.5:raise ValueError('World projection mismatch '+c['k'])
    audit.append(dict(city=c['k'],projection=c.get('lt',{}).get('kind','Albers'),centre_offset_km=round(float(err),2)))
for s in D['v20_ext']['airports']:
    c=raws[s['city']];same=[a for a in c['air'] if a['n']==s['zh']]
    if same:s['c']=ll(c,np.array(same[0]['c'])/20).tolist()
    if s['c'][0]>60 or s['c'][0]<-15 or s['c'][1]<10 or s['c'][1]>55:raise ValueError('Roman airport outside expected region')
for obj in files.values():
    if 'l_city.json' in obj:obj['l_city.json']=encode(C)
for p,obj in files.items():p.write_text(p.read_text().split('=',1)[0]+'='+dumps(obj)+';')
(O/'data/v20_d.js').write_text('document.getElementById("data").textContent='+json.dumps(encode(D))+';')
(O/'world-coordinates-v20.json').write_text(json.dumps({'cities':audit,'Roman_airports':len(D['v20_ext']['airports']),'projection_checks':'pass'},ensure_ascii=False,indent=2))
# Draw added partitions and routes after background fills, then place labels.
p=O/'index.html';h=p.read_text().replace('extensionGround20(zl);drawDist();','drawDist();')
h=h.replace('ctx.setTransform(dpr,0,0,dpr,0,0);drawPoints();labels();\n  nDraw();','nDraw();extensionGround20(zoomLevel());\n  ctx.setTransform(dpr,0,0,dpr,0,0);drawPoints();labels();')
p.write_text(h)
print('Checked',len(audit),'world city projections and 29 Roman airports')
