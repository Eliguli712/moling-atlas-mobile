"""Conservative island transport and a generalized Six Dynasties Xuanwu Lake.

This patches the retained v20 data; frontier and maritime ownership are immutable.
"""
from pathlib import Path
import json,math,copy,hashlib
import numpy as np
from shapely.geometry import Point,Polygon,LineString,box
from shapely.ops import unary_union,nearest_points,transform
from revise_atlas_v20 import decode,encode,dumps,xy,delta,pack,polygons
R=Path(__file__).resolve().parent.parent;O=R/'dist';files={};A={};owners={}
for p in sorted((O/'data').glob('*a*.js')):
 obj=json.loads(p.read_text().split('=',1)[1].strip().rstrip(';'));files[p]=obj
 for k,v in obj.items():A[k]=v;owners[k]=p
dp=O/'data/v20r3_d.js';D=decode(json.loads(dp.read_text().split('=',1)[1].strip().rstrip(';')));P=D['proj'];C=decode(A['l_city.json'])
protected=['p500','wei17','wei_nominal_v15','nomad_area_v16']
before={k:hashlib.sha256(dumps(D[k]).encode()).hexdigest() for k in protected}
def fwd(ll):
 a=np.asarray(ll,float);lo=np.radians(a[...,0]);la=np.radians(a[...,1]);e=math.sqrt(P['E2']);ss=np.sin(la)
 q=(1-P['E2'])*(ss/(1-P['E2']*ss*ss)-np.log((1-e*ss)/(1+e*ss))/(2*e));rho=P['RA']*np.sqrt(P['C']-2*P['N']*q/P['QP'])/P['N'];th=P['N']*(lo-P['L0'])
 return np.stack([rho*np.sin(th)/1000,(P['RHO0']-rho*np.cos(th))/1000],axis=-1)
def inv(a):
 a=np.asarray(a,float);x=a[...,0]*1000;y=a[...,1]*1000;e=math.sqrt(P['E2']);rho=np.hypot(x,P['RHO0']-y);th=np.arctan2(x,P['RHO0']-y);q=P['QP']*(P['C']-(rho*P['N']/P['RA'])**2)/(2*P['N']);la=np.arcsin(np.clip(q/P['QP'],-1,1))
 for _ in range(8):
  ss=np.sin(la);v=(1-P['E2'])*(ss/(1-P['E2']*ss*ss)-np.log((1-e*ss)/(1+e*ss))/(2*e));la+=(q-v)/(2*(1-P['E2'])*np.cos(la)/(1-P['E2']*ss*ss)**2)
 return np.stack([(th/P['N']+P['L0'])*180/np.pi,la*180/np.pi],axis=-1)
def local(c,ll):
 p=fwd(ll);return np.stack([p[...,0]-c['o'][0],c['o'][1]-p[...,1]],axis=-1)
def world(c,p):
 p=np.asarray(p);return inv(np.stack([c['o'][0]+p[...,0],c['o'][1]-p[...,1]],axis=-1))
def put(k,obj):
 # Override every duplicate dictionary occurrence so load order is irrelevant.
 for p,items in files.items():
  if k in items:items[k]=encode(obj)
 A[k]=encode(obj)

# Land model limited to Taiwan; no union of unrelated world rings or frontier edits.
roi=box(119.5,21.5,122.5,26);land=[]
for r in D['world']:
 a=xy(r,10000)
 if np.max(a[:,0])<119.5 or np.min(a[:,0])>122.5 or np.max(a[:,1])<21.5 or np.min(a[:,1])>26:continue
 g=Polygon(a).buffer(0).intersection(roi)
 if not g.is_empty:land.append(g)
land=unary_union(land)
configs=[('danshui',True,8,[.65,-.76]),('dadu',False,6,[.15,-.99]),('taijiang',True,9,[.12,-.99]),('lanyang',False,6,[.35,-.94]),('hualien',False,6,[-.12,-.99]),('beinan',False,6,[.4,-.92])]
audit=[];hubs={};oldstations=0
for slug,metro,nst,direction in configs:
 k='qv20_'+slug;c=decode(A['c/'+k+'.json']);s=next(s for s in C['city'] if s['k']==k);oldstations+=len(c['mn'])
 pland=transform(lambda x,y,z=None:(local(c,np.column_stack([x,y]))[:,0],local(c,np.column_stack([x,y]))[:,1]),land).intersection(box(.5,.5,c['w']-.5,c['w']-.5)).buffer(-.08)
 water=unary_union([Polygon(xy(l['r'])).buffer(0) for l in c['sea']+c['lake'] if not l.get('h')])
 pland=pland.difference(water.buffer(.12))
 centre=local(c,[s['lon'],s['lat']]);v=np.asarray(direction);v/=np.linalg.norm(v);normal=np.array([-v[1],v[0]]);length=8.4 if metro else 5.6
 # Search a short settlement corridor, avoiding sea with no artificial sinusoid.
 best=None
 for shift in np.linspace(-4,4,65):
  for along in [0,-.8,.8]:
   mid=centre+normal*shift+v*along;a=mid-v*length/2;b=mid+v*length/2;line=LineString([a,b]);outside=line.difference(pland).length
   score=outside*100+abs(shift)+abs(along)
   if best is None or score<best[0]:best=(score,line)
 line=best[1]
 if line.difference(pland).length>.03:
  pieces=[g for g in getattr(line.intersection(pland),'geoms',[line.intersection(pland)]) if g.geom_type=='LineString']
  line=max(pieces,key=lambda g:g.length)
 # Even station intervals; every stop lies exactly on the route.
 stops=np.asarray([line.interpolate(i/(nst-1),normalized=True).coords[0] for i in range(nst)])
 assert line.length/(nst-1)>.48,(k,line.length)
 names=[s['n']+x for x in (['南坊','学舍','西市','城心','北市','河津','驿前','北坊','新聚'][:nst])];hub=nst//2;names[hub]=s['n']+'干线换乘';hubs[slug]=world(c,stops[hub]).tolist()
 col='#226d8b' if metro else '#4a8a65';name=s['n']+('城津线' if metro else '聚落电车');q=delta(stops)
 route=dict(n=name,col=col,k='line' if metro else 'tram',s='规划',ring=0,km=round(line.length,2),q=q,op=0,xr=[])
 c['ml']=[];c['mn']=[];c['lrt']=[];c['xf']=[];s['ml']=[];s['ms']=[];s['lr']=[];s['lst']=[]
 if metro:
  route['nd']=list(range(nst));c['ml']=[route];c['mn']=[dict(n=n,c=np.round(p*20,3).tolist(),l=[0],s=np.round((p-centre)*2,3).tolist()) for n,p in zip(names,stops)]
  s['ml']=[dict(n=name,col=col,s='规',q=delta(world(c,stops),10000))];s['ms']=[dict(n=n,c=np.round(ll,6).tolist(),i=False,w=4 if i in [0,hub,nst-1] else 1) for i,(n,ll) in enumerate(zip(names,world(c,stops)))]
 else:
  route['st']=[dict(n=n,c=np.round(p*20,3).tolist()) for n,p in zip(names,stops)];c['lrt']=[route];s['lr']=[dict(n=name,k='tram',col=col,s='规',q=delta(world(c,stops),10000))];s['lst']=[dict(n=n,c=np.round(ll,6).tolist(),local=np.round(p*20,3).tolist(),lines=[name],col=col,k='tram') for n,ll,p in zip(names,world(c,stops),stops)]
 # Short through-city surface rail shares the exact central transfer coordinate.
 rail=LineString([stops[hub]-v*min(7,line.length),stops[hub]+v*min(7,line.length)]).intersection(box(.2,.2,c['w']-.2,c['w']-.2))
 c['rail']=[dict(n='台湾环岛铁路',k='rail',q=delta(rail.coords),s='规划')];c['rst']=[dict(n=names[hub],k='rail',c=np.round(stops[hub]*20,3).tolist())]
 c['metro']=dict(nl=1 if metro else 0,km=0,kmp=round(line.length,2) if metro else 0,total_km=round(line.length,2) if metro else 0,nst=nst if metro else 0,ring=0,lrtkm=0 if metro else round(line.length,2),xpkm=0)
 c['stats']['nst']=len(c['mn']);c['metro_note']='保守方案：优先沿聚落、港津和既有街道布设一条'+('地铁走廊' if metro else '地面电车走廊')+'；干线站集中换乘，无城市环线。线路属于架空规划。'
 s.update(nl=c['metro']['nl'],km=0,planned_km=c['metro']['kmp'],transport_plan='v21 conservative');c['transport_revision_v21']={'mode':'metro' if metro else 'tram','stations':nst,'interval_km':round(line.length/(nst-1),3),'detour_ratio':1.0,'hub':hubs[slug]}
 put('c/'+k+'.json',c);audit.append(dict(city=k,**c['transport_revision_v21']))

# Both rings pass the city transfer nodes. North/east use valleys and designated
# tunnel corridors; no metro ring around the island, no eastern motorway.
ring=[hubs['danshui'],[121.39,25.02],[121.25,24.83],[121.02,24.77],[120.86,24.57],[120.70,24.36],hubs['dadu'],[120.49,23.96],[120.42,23.72],[120.33,23.48],[120.25,23.25],hubs['taijiang'],[120.27,22.83],[120.37,22.64],[120.52,22.52],[120.66,22.44],[120.80,22.36],[120.92,22.39],[121.01,22.58],hubs['beinan'],[121.20,22.92],[121.23,23.12],[121.33,23.34],[121.42,23.57],[121.50,23.79],hubs['hualien'],[121.63,24.13],[121.70,24.29],[121.77,24.46],hubs['lanyang'],[121.80,24.83],[121.85,24.94],[121.81,25.05],[121.69,25.10],[121.56,25.13],hubs['danshui']]
oldroutes=D['v20_ext']['routes'];oldroutes[:]=[r for r in oldroutes if not r['n'].startswith('台湾')]
for slug,_,_,_ in configs:
 k='qv20_'+slug;c=decode(A['c/'+k+'.json']);track=LineString(local(c,ring)).intersection(box(.2,.2,c['w']-.2,c['w']-.2));parts=[g for g in getattr(track,'geoms',[track]) if g.geom_type=='LineString'];c['rail']=[dict(n='台湾环岛铁路',k='rail',q=delta(g.coords),s='规划') for g in parts];put('c/'+k+'.json',c)
for name,el,kind in [('台湾环岛铁路','Περιμετρικός σιδηρόδρομος της Ταϊβάν','rail'),('台湾环岛公路','Περιμετρική οδός της Ταϊβάν','road')]:
 oldroutes.append(dict(n=name,el=el,kind=kind,q=delta(ring,10000),ends=[ring[0],ring[-1]],stops=[next(s['n'] for s in C['city'] if s['k']=='qv20_'+k) for k in ['danshui','dadu','taijiang','beinan','hualien','lanyang']],s='规划',closed=True,standard='西岸干线；东岸与南段按山麓和河谷布设普通公路' if kind=='road' else '常规铁路；苏花、南回采用隧道廊道；避开中央山脉',stations=[dict(n=k,c=p) for k,p in hubs.items()]))

# Generalized historical lake, not a claim of a surveyed 497 shoreline.
lake_ll=np.array([[118.765,32.082],[118.766,32.071],[118.778,32.064],[118.791,32.064],[118.804,32.067],[118.816,32.072],[118.825,32.081],[118.829,32.091],[118.821,32.103],[118.806,32.110],[118.788,32.108],[118.778,32.102],[118.765,32.101],[118.751,32.105],[118.746,32.100],[118.756,32.093],[118.765,32.090]])
lake_ll=np.array([118.794,32.086])+(lake_ll-[118.794,32.086])*math.sqrt(15.12/25.48)
lake=Polygon(lake_ll);capital=decode(A['c/q0000.json']);llocal=local(capital,lake_ll)
capital['lake'].append(dict(n='玄武湖',el='Λίμνη Σιουανουού',h=0,r=delta(llocal),historical_period='六朝',shoreline='概化示意'))
capital['hydrology_labels'].append(dict(n='玄武湖 · 后湖',c=np.round(local(capital,[118.796,32.085])*20,3).tolist(),k='lake'))
capital['xuanwu_v21']={'n':'玄武湖','period':'497 / 六朝','shoreline':'历史水域概化，不作为精确古岸线','source':'https://www.xuanwuhu.net/mhls/mhls1.aspx','r':delta(llocal)}
put('c/q0000.json',capital)
H=decode(A['l_hyd.json']);H['lake'].append(dict(n='玄武湖',el='Λίμνη Σιουανουού',k='lake',a=round(Polygon(fwd(lake_ll)).area,2),d=2,s='497',lon=118.796,lat=32.085,r=pack(lake),b=[],focus=True,note='六朝水域概化；北湖、后湖，皇家苑囿与水军阅武水域'))
put('l_hyd.json',H)
next(s for s in C['city'] if s['k']=='q0000')['hy'].append(dict(n='玄武湖 · 后湖',k='lake',c=[118.796,32.085]))
put('l_city.json',C)
D['c20']['nm']-=4;D['c20']['new_planned_metro_lines']-=16;D['c20']['nst']+=17-oldstations;D['c20']['new_planned_light_lines']=4
D['v21']={'revision':'v21','taiwan_metro_lines':2,'taiwan_tram_lines':4,'taiwan_stops':sum(c['stations'] for c in audit),'xuanwu_lake_km2':H['lake'][-1]['a']}
after={k:hashlib.sha256(dumps(D[k]).encode()).hexdigest() for k in protected};assert before==after
for p,obj in files.items():
 old=p.read_text();new=old.split('=',1)[0]+'='+dumps(obj)+';'
 if old!=new:p.write_text(new)
dp.write_text('document.getElementById("data").textContent='+json.dumps(encode(D))+';')
report={'revision':'v21','taiwan':audit,'ring_end_gap':float(np.linalg.norm(np.array(ring[0])-ring[-1])),'xuanwu_lake_km2':H['lake'][-1]['a'],'protected_frontiers_sha256':after,'frontier_and_maritime_ownership_unchanged':True,'source_urls':['https://www.xuanwuhu.net/mhls/mhls1.aspx','https://www.xuanwuhu.net/mhls/detail.aspx?id=242']}
(O/'validation-v21.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(dumps(report))
