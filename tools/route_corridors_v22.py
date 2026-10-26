"""Trace continuous geographic corridors; never create city-to-city chords.

Modern OSM/Natural Earth alignments are geographic references for this fictional
497 planning layer. They do not assert that these railways existed in 497.
The compact selected reference geometries are retained for reproducibility.
"""
from pathlib import Path
import json,math,hashlib,collections,ijson,copy
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components,dijkstra
from shapely.geometry import LineString,shape,box
from shapely.ops import unary_union
from revise_atlas_v20 import decode,encode,dumps,xy,delta
R=Path(__file__).resolve().parents[1]; O=R/'dist'; RAW=R.parent/'analysis/rail22'

class Network:
 def __init__(self,name,mode,ordinary=False):
  self.name=name; self.mode=mode; self.sources=[]; self.gov=name=='taiwan' and mode=='road' and (RAW/'taiwan-gov-roads.json').exists();segments=[]
  osm=RAW/f'{name}-{mode}.json'
  if name=='hainan' and mode=='road' and (RAW/'hainan-roads-full.json').exists():osm=RAW/'hainan-roads-full.json'
  if osm.exists() and not self.gov and not (name=='taiwan' and mode=='rail'):
   self.sources=['OpenStreetMap'];self.osm=True
   # Stream large regional extracts; retain shared OSM nodes during reduction.
   counts=collections.Counter()
   with osm.open('rb') as stream:
    for w in ijson.items(stream,'elements.item'):counts.update(w.get('nodes',[]))
   with osm.open('rb') as stream:
    for w in ijson.items(stream,'elements.item'):
     tags=w.get('tags',{})
     if ordinary and ((tags.get('highspeed')=='yes' and '丹大' not in tags.get('name','')) or any(s in tags.get('name','') for s in ['高速','客运专线','客专','高鐵','高铁'])):continue
     if tags.get('usage') in ['military'] or tags.get('railway') in ['abandoned','disused','construction']:continue
     p=[(float(v['lon']),float(v['lat'])) for v in w.get('geometry',[]) if v]
     if len(p)<2:continue
     stops=sorted(set([0,len(p)-1]+[i for i,nid in enumerate(w.get('nodes',[])) if counts[nid]>1]))
     reduced=[]
     for a,b in zip(stops,stops[1:]):
      reduced.extend(list(LineString(p[a:b+1]).simplify(.000035).coords)[:-1])
     reduced.append(p[-1]);segments.append(reduced if name=='south-china' else p)
   del counts
  else:
   self.osm=False;self.sources=['內政部國土測繪中心：國道及省道道路中線（1150409）'] if self.gov else ['Natural Earth 1:10m']
   p=RAW/'taiwan-gov-roads.json' if self.gov else RAW/f'{name}-ne-{"railroads" if mode=="rail" else "roads"}.json'
   lines=[shape(f['geometry']) for f in json.loads(p.read_text())['features']]
   # Node the reference network at its real junctions before graph routing.
   u=unary_union(lines);segments=[list(g.coords) for g in (u.geoms if hasattr(u,'geoms') else [u])]
  self.segments=segments
  self.scale=np.array([111.195*math.cos(math.radians(np.mean([p[0][1] for p in segments]))),111.195])
  ids={};points=[];edges={}
  def node(p):
   k=tuple(np.round(p,5))
   if k not in ids:ids[k]=len(points);points.append(p)
   return ids[k]
  for line in segments:
   ns=[node(p) for p in line]
   for a,b in zip(ns,ns[1:]):
    if a==b:continue
    e=tuple(sorted((a,b)));edges[e]=float(np.linalg.norm((np.array(points[a])-points[b])*self.scale))
  self.p=np.asarray(points);self.tree=cKDTree(self.p*self.scale)
  def graph():
   rows=[];cols=[];weights=[]
   for (a,b),w in edges.items():rows.extend([a,b]);cols.extend([b,a]);weights.extend([w,w])
   return coo_matrix((weights,(rows,cols)),shape=(len(points),)*2).tocsr()
  g=graph();_,cc=connected_components(g,directed=False)
  # Join only survey/rounding gaps under 80 m, never remote city endpoints.
  # This also joins the two tracks at station throats in OSM's sparse data.
  pairs=self.tree.query_pairs(.08 if self.osm or self.gov else 2.0,output_type='ndarray'); joins=0
  parent=np.arange(int(max(cc))+1)
  def root(c):
   while parent[c]!=c:parent[c]=parent[parent[c]];c=parent[c]
   return c
  if len(pairs):
   ds=np.linalg.norm((self.p[pairs[:,0]]-self.p[pairs[:,1]])*self.scale,axis=1)
   for index in np.argsort(ds):
    a,b=pairs[index];aa,bb=root(cc[a]),root(cc[b])
    if (self.osm and cc[a]!=cc[b]) or (not self.osm and aa!=bb):
     edges[(int(a),int(b))]=float(ds[index]);parent[aa]=bb;joins+=1
  self.g=graph();_,self.cc=connected_components(self.g,directed=False);self.joins=joins
  sizes=collections.Counter(self.cc);self.components=[c for c,n in sizes.most_common() if n>20]
  self.ctrees={c:(np.flatnonzero(self.cc==c),cKDTree(self.p[self.cc==c]*self.scale)) for c in self.components[:100]}
  print(name,mode,'nodes',len(points),'components',sizes.most_common(5),'tiny gap joins',joins,flush=True)
 def snap(self,waypoints):
  w=np.asarray(waypoints);choices=[]
  for c,(ids,tree) in self.ctrees.items():
   dd,ii=tree.query(w*self.scale)
   choices.append((float(np.max(dd)+np.mean(dd)*.5),dd,ids[ii]))
  _,dd,ns=min(choices,key=lambda x:x[0])
  if max(dd)>35:raise ValueError(f'{self.name} {self.mode}: remote corridor snap {dd}')
  return list(map(int,ns)),dd
 def route(self,waypoints):
  ns,dd=self.snap(waypoints)
  if not hasattr(self,'hubs'):self.hubs={}
  # Map matching weighs both station proximity and continuity. A nearby branch
  # that requires hundreds of km of backtracking cannot win on proximity alone.
  if self.osm and self.name!='south-china':
   component=self.cc[ns[0]];ids,tree=self.ctrees[component];layers=[]
   closed=np.linalg.norm(np.array(waypoints[0])-waypoints[-1])<.00001
   for i,w in enumerate(waypoints):
    key=tuple(np.round(w,6))
    if key in self.hubs:choices=[self.hubs[key]]
    elif closed and i==len(waypoints)-1:choices=layers[0]
    else:
     near=tree.query_ball_point(np.array(w)*self.scale,max(12,float(dd[i])+8));near=sorted(near,key=lambda k:np.linalg.norm((self.p[ids[k]]-w)*self.scale));choices=[]
     for k in near:
      nid=int(ids[k])
      if all(np.linalg.norm((self.p[nid]-self.p[j])*self.scale)>1.2 for j in choices):choices.append(nid)
      if len(choices)>=10:break
     if not choices:choices=[ns[i]]
    if closed and i==0:choices=[ns[0]]
    layers.append(choices)
   costs=np.linalg.norm((self.p[layers[0]]-waypoints[0])*self.scale,axis=1)*6;history=[]
   for i in range(1,len(layers)):
    dist,prev=dijkstra(self.g,directed=False,indices=layers[i-1],return_predecessors=True)
    score=costs[:,None]+dist[:,layers[i]];parents=np.argmin(score,axis=0)
    costs=score[parents,np.arange(len(layers[i]))]+np.linalg.norm((self.p[layers[i]]-waypoints[i])*self.scale,axis=1)*6
    history.append((parents,prev))
   k=int(np.argmin(costs));chosen=[layers[-1][k]];parts=[]
   for i in range(len(layers)-1,0,-1):
    parents,prev=history[i-1];pk=int(parents[k]);a=layers[i-1][pk];b=layers[i][k];q=[b]
    while q[-1]!=a:q.append(int(prev[pk,q[-1]]))
    parts.append(q[::-1]);chosen.append(a);k=pk
   ns=chosen[::-1];nodes=[]
   for q in parts[::-1]:nodes.extend(q[:-1])
   nodes.append(ns[-1]);dd=np.linalg.norm((self.p[ns]-np.array(waypoints))*self.scale,axis=1)
   for w,nid in zip(waypoints,ns):self.hubs[tuple(np.round(w,6))]=nid
  else:
   nodes=[]
   for a,b in zip(ns,ns[1:]):
    if a==b:continue
    ds,prev=dijkstra(self.g,directed=False,indices=a,return_predecessors=True)
    if not np.isfinite(ds[b]):raise ValueError('Disconnected reference network')
    q=[b]
    while q[-1]!=a:q.append(int(prev[q[-1]]))
    nodes.extend(q[::-1][:-1])
   nodes.append(ns[-1])
  p=self.p[nodes];keep=np.r_[True,np.any(np.diff(np.round(p,7),axis=0),axis=1)];p=p[keep]
  return p,self.p[ns],dd

def build():
 dp=O/'data/v21_d.js' if (O/'data/v21_d.js').exists() else O/'data/v22_d.js';D=decode(json.loads(dp.read_text().split('=',1)[1].strip().rstrip(';')))
 D['v20_ext']['routes']=json.loads((R/'tools/base-corridors-v21.json').read_text())
 protected={k:hashlib.sha256(dumps(D[k]).encode()).hexdigest() for k in ['p500','wei17','world','v20_border']}
 nets={};report=[];selected=[]
 def net(region,mode):
  key=(region,mode)
  if key not in nets:nets[key]=Network(region,mode,region in ['liaodong','taiwan'])
  return nets[key]
 # Through-points are towns at valley / foothill junctions, not a schematic grid.
 plans={
  0:('south-china','road',[[106.05,21.18],[106.7,22.1],[108.37,22.82],[109.2,21.67],[110.36,21.27],[111.97,21.85],[113.26,23.13]]),
  1:('south-china','rail',[[106.05,21.18],[106.7,22.1],[108.37,22.82],[109.4,24.3],[110.29,25.27]]),
  2:('south-china','road',[[111.3,23.48],[111.55,24.4],[110.29,25.27],[112.6,26.9],[112.98,28.2]]),
  3:('south-china','road',[[108.37,22.82],[109.2,21.67]]),
  4:('south-china','rail',[[105.73,21.24],[105.85,21.03],[106.05,21.18]]),
  5:('south-china','road',[[105.85,21.03],[107.1,21.05],[107.97,21.55],[109.2,21.67],[110.36,21.27],[111.97,21.85],[113.26,23.13]]),
  6:('south-china','road',[[111.3,23.48],[111.55,24.4],[110.29,25.27],[112.6,26.9],[112.98,28.2]]),
  7:('south-china','road',[[109.2,21.67],[110.36,21.27],[110.17,20.28]]),
 10:('hainan','road',[[110.33,20.0],[110.75,19.61],[110.43,19.19],[110.04,18.73],[109.5,18.27],[109.17,18.52],[108.69,19.1],[109.03,19.6],[110.33,20.0]]),
 11:('hainan','road',[[110.35,19.94],[110.1,19.25],[109.84,19.03],[109.67,18.78],[109.5,18.25]]),
 12:('byzantium','road',[[23.32,42.7],[26.56,41.67],[28.98,41.01],[32.85,39.93],[35.48,38.73]]),
 13:('byzantium','road',[[29.73,40.43],[29.98,39.43],[27.14,38.42],[27.43,37.03]]),
 14:('byzantium','road',[[36.16,36.2],[36.7,34.73],[36.3,33.5],[35.23,31.77],[32.34,30.56],[31.24,30.04],[29.92,31.2]]),
 15:('byzantium','road',[[23.32,42.7],[23.12,41.56],[22.94,40.64],[22.42,39.64],[23.73,37.98]]),
 16:('south-china','road',[[103.7155,25.0692],[103.43,24.4],[106.6,23.9],[108.37,22.82]]),
 }
 ring=[[121.51,25.047],[120.55,24.16],[120.2,23.01],[120.52,22.38],[121.1226,22.7844],[121.59,23.995],[121.77,24.6845],[121.51,25.047]]
 plans[17]=('taiwan','rail',ring);plans[18]=('taiwan','road',[[121.45,25.14],[120.55,24.16],[120.2,23.01],[120.74,21.98],[121.1226,22.7844],[121.59,23.995],[121.77,24.6845],[121.45,25.14]])
 for i in range(19,23):plans[i]=('liaodong','rail',[s['c'] for s in D['v20_ext']['routes'][i]['stations']])
 plans[19][2][3]=[122.747,40.853]
 plans[19][2][4]=[122.35,40.4]
 oldaux=copy.deepcopy(D['v20_ext']['routes'][20]);main=D['v20_ext']['routes'][19];freight=D['v20_ext']['routes'][22]
 aux=D['v20_ext']['routes'][20]
 aux['stations']=[copy.deepcopy(main['stations'][0]),copy.deepcopy(main['stations'][1]),copy.deepcopy(oldaux['stations'][2]),{'n':'凤凰谷口','c':[124.067,40.453]},copy.deepcopy(freight['stations'][3]),copy.deepcopy(oldaux['stations'][5]),copy.deepcopy(oldaux['stations'][6]),copy.deepcopy(main['stations'][-1])]
 aux['stops']=[s['n'] for s in aux['stations']];plans[20]=('liaodong','rail',[s['c'] for s in aux['stations']])
 branch=copy.deepcopy(oldaux);branch.update(n='岫岩—庄河山地支线',el='Ορεινός κλάδος Σιουγιάν–Τζουανγκχέ',stations=[copy.deepcopy(oldaux['stations'][4]),copy.deepcopy(oldaux['stations'][5])]);branch['stops']=[s['n'] for s in branch['stations']]
 D['v20_ext']['routes'].append(branch);plans[23]=('liaodong','rail',[s['c'] for s in branch['stations']])
 for i,(region,mode,wp) in plans.items():
  l=D['v20_ext']['routes'][i];n=net(region,mode)
  p,st,dd=n.route(wp)
  if n.gov:p=np.asarray(LineString(p*n.scale).simplify(.004).coords)/n.scale
  if i in [10,17,18]:p[-1]=p[0];l['closed']=True
  if len(p)<8:raise ValueError('Insufficient corridor geometry '+l['n'])
  l.update(q=delta(p,10000),ends=[p[0].tolist(),p[-1].tolist()],km=round(float(np.linalg.norm(np.diff(p,axis=0)*n.scale,axis=1).sum()),1),standard='按连续铁路／公路参考廊道保留地形转折、桥隧与河谷；497架空规划',reference={'source':n.sources,'license':'政府資料開放授權條款第1版' if n.gov else 'ODbL 1.0' if n.osm else 'public domain','revision':'v22'})
  if i>=19:
   for s,c in zip(l['stations'],st):s['city_center']=s['c'];s['c']=c.tolist();s['type']='城郊接轨站'
  elif i in [17,18]:
   # Preserve six named interchange locations; use the nearest point ON the line.
   tree=cKDTree(p*n.scale)
   for s in l['stations']:
    s['city_center']=s['c'];_,j=tree.query(np.array(s['c'])*n.scale);s['c']=p[j].tolist()
  steps=np.linalg.norm(np.diff(p,axis=0)*n.scale,axis=1)
  row=dict(name=l['n'],region=region,mode=mode,source=n.sources,vertices=len(p),km=l['km'],largest_reference_segment_km=round(float(max(steps)),3),station_snap_km=np.round(dd,2).tolist(),city_to_city_chords_added=0)
  report.append(row);selected.append({'type':'Feature','properties':{'name':l['n'],'route_index':i,'entry':{k:v for k,v in l.items() if k!='q'},'validation':row,'source':n.sources,'license':l['reference']['license']},'geometry':{'type':'LineString','coordinates':np.round(p,7).tolist()}})
  print(l['n'],len(p),l['km'],'snap',np.round(dd,1).tolist(),flush=True)
 for k,h in protected.items():assert hashlib.sha256(dumps(D[k]).encode()).hexdigest()==h,k
 D['v20_ext']['corridors_v22']={'credit':'© OpenStreetMap contributors, ODbL 1.0; Natural Earth, public domain','urls':['https://www.openstreetmap.org/copyright','https://www.naturalearthdata.com/','https://www.igsnrr.cas.cn/cbkx/kpyd/zgdl/cnh/202009/t20200910_5692432.html'],'note':'现代线路只作为497架空规划的地形廊道参考。城郊站接入连续路网，不强行把城中心用直线连到线路。'}
 if any(n.gov for n in nets.values()):
  D['v20_ext']['corridors_v22']['credit']+='；台湾道路：內政部國土測繪中心，政府資料開放授權條款第1版'
  D['v20_ext']['corridors_v22']['urls'].append('https://data.gov.tw/dataset/73232')
 (O/'data/v22_d.js').write_text('document.getElementById("data").textContent='+json.dumps(encode(D))+';')
 (R/'tools/corridors-v22.geojson').write_text(dumps({'type':'FeatureCollection','attribution':D['v20_ext']['corridors_v22'],'features':selected}))
 (O/'corridors-v22.json').write_text(json.dumps({'revision':'v22','routes':report,'protected_data_sha256':protected,'synthetic_long_connectors':0,'attribution':D['v20_ext']['corridors_v22']},ensure_ascii=False,indent=2))
 print('Rebuilt',len(report),'corridors')

def restore_selected():
 """Reproduce the chosen corridors without downloading a regional OSM extract."""
 p=O/'data/v22_d.js'
 if not p.exists():p=O/'data/v21_d.js'
 D=decode(json.loads(p.read_text().split('=',1)[1].strip().rstrip(';')))
 selected=json.loads((R/'tools/corridors-v22.geojson').read_text())
 routes=json.loads((R/'tools/base-corridors-v21.json').read_text())
 for f in selected['features']:
  a=f['properties'];i=a['route_index']
  while len(routes)<=i:routes.append({})
  routes[i]={**a['entry'],'q':delta(f['geometry']['coordinates'],10000)}
 D['v20_ext']['routes']=routes;D['v20_ext']['corridors_v22']=selected['attribution']
 (O/'data/v22_d.js').write_text('document.getElementById("data").textContent='+json.dumps(encode(D))+';')
 print('Restored',len(selected['features']),'chosen reference corridors')

if __name__=='__main__':
 import sys
 if '--retrace' in sys.argv or not (R/'tools/corridors-v22.geojson').exists():build()
 else:restore_selected()
