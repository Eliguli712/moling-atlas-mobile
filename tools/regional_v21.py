"""Terrain cost corridors and island catchment partitions for the v21 atlas."""
from pathlib import Path
import json,math,heapq,hashlib
import numpy as np
import shapely
from shapely.geometry import Polygon,LineString,Point,box,shape,mapping
from shapely.ops import unary_union,transform,nearest_points
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from revise_atlas_v20 import decode,encode,dumps,xy,delta,pack,polygons
R=Path(__file__).resolve().parent.parent;O=R/'dist';dp=O/'data/v20r3_d.js';D=decode(json.loads(dp.read_text().split('=',1)[1].strip().rstrip(';')))
A={}
for p in sorted((O/'data').glob('*a*.js')):A.update(json.loads(p.read_text().split('=',1)[1].strip().rstrip(';')))
relief=decode(A['global-relief.json'])['tiles'];coasts=json.loads((R/'tools/island-coasts-v21.geojson').read_text());coast={f['properties']['name']:shape(f['geometry']) for f in coasts['features']}
wei=next(s for s in D['p500'] if s['en']=='Toba Wei');before=hashlib.sha256(dumps(wei).encode()).hexdigest()
class Terrain:
 def __init__(self,bounds,step=2,land=None):
  self.bounds=bounds;self.step=step;self.lo=(bounds[0]+bounds[2])/2;self.la=(bounds[1]+bounds[3])/2;self.cs=math.cos(math.radians(self.la));self.scale=np.array([111.195*self.cs,111.195]);self.origin=np.array([self.lo,self.la])
  self.project=lambda a:(np.asarray(a)-self.origin)*self.scale
  self.inverse=lambda a:np.asarray(a)/self.scale+self.origin
  a,b=self.project([bounds[:2],bounds[2:]]);self.x=np.arange(a[0],b[0]+step,step);self.y=np.arange(a[1],b[1]+step,step);self.xx,self.yy=np.meshgrid(self.x,self.y);self.h,self.w=self.xx.shape
  if land is None:
   gs=[];roi=box(*bounds)
   for r in D['world']:
    p=xy(r,10000)
    if np.max(p[:,0])<bounds[0] or np.min(p[:,0])>bounds[2] or np.max(p[:,1])<bounds[1] or np.min(p[:,1])>bounds[3]:continue
    g=Polygon(p).buffer(0).intersection(roi)
    if not g.is_empty:gs.append(g)
   land=unary_union(gs)
  self.land_ll=land;self.land=transform(lambda x,y,z=None:((np.asarray(x)-self.lo)*self.scale[0],(np.asarray(y)-self.la)*self.scale[1]),land)
  self.mask=shapely.contains_xy(self.land.buffer(.4),self.xx,self.yy);self.safe=shapely.contains_xy(self.land.buffer(-.25),self.xx,self.yy)
  pts=[];heights=[]
  for t in relief:
   if t['e']<=0 or t['e']>4000:continue
   l,b,r,u=t['b']
   if r<bounds[0] or l>bounds[2] or u<bounds[1] or b>bounds[3]:continue
   for q in t['q']:
    p=xy(q,10000);p=p[(p[:,0]>=bounds[0])&(p[:,0]<=bounds[2])&(p[:,1]>=bounds[1])&(p[:,1]<=bounds[3])][::2]
    pts.extend(self.project(p));heights.extend([t['e']]*len(p))
  # Coast points constrain the interpolation to sea level.
  for p in polygons(self.land):
   a=np.asarray(p.exterior.coords);pts.extend(a[::max(1,len(a)//500)]);heights.extend([0]*len(a[::max(1,len(a)//500)]))
  dem=griddata(pts,heights,(self.xx,self.yy),method='linear');near=griddata(pts,heights,(self.xx,self.yy),method='nearest');self.dem=gaussian_filter(np.where(np.isfinite(dem),dem,near),.8);self.dem=np.maximum(self.dem,0);gy,gx=np.gradient(self.dem,step*1000);self.slope=np.hypot(gx,gy);self.cost=1+35*self.slope+1.5*(self.dem/800)**2
  self.land_cells=np.column_stack(np.nonzero(self.safe));self.tree=cKDTree(np.column_stack([self.x[self.land_cells[:,1]],self.y[self.land_cells[:,0]]]))
  self.edge_ok={}
 def node(self,ll):
  _,i=self.tree.query(self.project(ll));r,c=self.land_cells[i];return int(r),int(c)
 def path(self,waypoints):
  nodes=[self.node(p) for p in waypoints];result=[]
  for start,end in zip(nodes,nodes[1:]):
   queue=[(0,start)];dist={start:0};prev={};closed=set()
   while queue:
    _,a=heapq.heappop(queue)
    if a in closed:continue
    if a==end:break
    closed.add(a)
    for dr,dc in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
     r,c=a[0]+dr,a[1]+dc
     if r<0 or c<0 or r>=self.h or c>=self.w or not self.safe[r,c]:continue
     if dr and dc and (not self.safe[a[0]+dr,a[1]] or not self.safe[a[0],a[1]+dc]):continue
     b=(r,c);key=tuple(sorted([a,b]))
     if key not in self.edge_ok:self.edge_ok[key]=self.land.covers(LineString([[self.x[a[1]],self.y[a[0]]],[self.x[c],self.y[r]]]))
     if not self.edge_ok[key]:continue
     length=self.step*math.hypot(dr,dc);grade=abs(self.dem[b]-self.dem[a])/(length*1000);nd=dist[a]+length*((self.cost[a]+self.cost[b])/2+35*grade)
     if nd<dist.get(b,float('inf')):dist[b]=nd;prev[b]=a;heapq.heappush(queue,(nd+self.step*math.hypot(r-end[0],c-end[1]),b))
   if end not in prev and end!=start:raise ValueError('No land corridor '+str((start,end)))
   a=end;part=[a]
   while a!=start:a=prev[a];part.append(a)
   result.extend(part[::-1][:-1])
  result.append(nodes[-1]);p=np.array([[self.x[c],self.y[r]] for r,c in result]);line=LineString(p).simplify(self.step*.42)
  if line.difference(self.land).length>.01:line=LineString(p)
  # Round only safe corners; no repeated loops or sinusoidal displacement.
  a=np.asarray(line.coords);rounded=[a[0]]
  for i in range(1,len(a)-1):
   v=a[i]-a[i-1];w=a[i+1]-a[i];r=min(.7,np.linalg.norm(v)*.24,np.linalg.norm(w)*.24);b=a[i]-v/np.linalg.norm(v)*r;c=a[i]+w/np.linalg.norm(w)*r;q=np.array([(1-t)**2*b+2*(1-t)*t*a[i]+t*t*c for t in np.linspace(0,1,4)])
   if self.land.covers(LineString(q)):rounded.extend(q)
   else:rounded.append(a[i])
  rounded.append(a[-1]);out=LineString(rounded)
  if out.difference(self.land).length>.01:out=line
  assert out.difference(self.land.buffer(.1)).length<.05
  return self.inverse(np.asarray(out.coords)),round(out.length,1)
 def partitions(self,seeds):
  # Shared ridge/valley cost graph, separately seeded activity catchments.
  active=shapely.contains_xy(self.land.buffer(self.step*1.5),self.xx,self.yy);ids=np.arange(self.h*self.w).reshape(self.h,self.w);rows=[];cols=[];weights=[]
  for dr,dc in [(0,1),(1,0),(1,1),(1,-1)]:
   rr,cc=np.mgrid[max(0,-dr):min(self.h,self.h-dr),max(0,-dc):min(self.w,self.w-dc)];ok=active[rr,cc]&active[rr+dr,cc+dc];aa=ids[rr[ok],cc[ok]];bb=ids[rr[ok]+dr,cc[ok]+dc];ww=self.step*math.hypot(dr,dc)*((self.cost[rr[ok],cc[ok]]+self.cost[rr[ok]+dr,cc[ok]+dc])/2);rows.extend([aa,bb]);cols.extend([bb,aa]);weights.extend([ww,ww])
  graph=coo_matrix((np.concatenate(weights),(np.concatenate(rows),np.concatenate(cols))),shape=(self.h*self.w,)*2).tocsr();starts=[self.node(p) for p in seeds];ds=dijkstra(graph,directed=False,indices=[ids[a] for a in starts]);labels=np.argmin(ds,axis=0).reshape(self.h,self.w)
  gs=[]
  for label in range(len(seeds)):
   spans=[]
   for r in range(self.h):
    cells=np.flatnonzero((labels[r]==label)&active[r]);splits=np.split(cells,np.where(np.diff(cells)>1)[0]+1)
    for z in splits:
     if len(z):spans.append(box(self.x[z[0]]-self.step/2,self.y[r]-self.step/2,self.x[z[-1]]+self.step/2,self.y[r]+self.step/2))
   gs.append(unary_union(spans))
  gs=list(shapely.coverage_simplify(gs,self.step*.85,simplify_boundary=False));out=[];taken=Polygon()
  for g in gs:
   g=g.intersection(self.land).difference(taken).buffer(0);out.append(g);taken=unary_union([taken,g])
  missing=self.land.difference(taken)
  for g in polygons(missing):
   i=min(range(len(out)),key=lambda i:out[i].distance(g.representative_point()));out[i]=unary_union([out[i],g])
  assert unary_union(out).symmetric_difference(self.land).area<.01
  return [transform(lambda x,y,z=None:(np.asarray(x)/self.scale[0]+self.lo,np.asarray(y)/self.scale[1]+self.la),g) for g in out]

terrain=Terrain([117.8,38.5,127,43],2)
routes=[
 ('辽东西岸纵贯主线','Δυτική κύρια γραμμή της Λιαοντόνγκ','main',[[124.05,42.35],[123.45,41.8],[123.1727,41.2578],[122.9,40.82],[122.47,40.4],[121.97,39.62],[121.72,39.12]],['辽河北口','浑河城','辽东城','安市城','建安城','复州津','卑沙城']),
 ('辽东东麓纵贯辅线','Ανατολική βοηθητική γραμμή της Λιαοντόνγκ','aux',[[124.05,42.35],[123.95,41.87],[123.75,41.3],[123.09,40.65],[123.28,40.29],[122.97,39.7],[122.43,39.65],[121.72,39.12]],['辽河北口','新城','太子河东站','析木河枢纽','岫岩谷口','庄河津','碧流河驿','卑沙城']),
 ('北魏—高句丽辽河货运联络线','Εμπορευματική σύνδεση Βορείου Οὐέι–Κογκουρυό','freight',[[120.4508,41.5801],[121.15,41.12],[122.2,41.35],[123.1727,41.2578]],['和龙','徒河接轨场','辽河联检站','辽东城']),
 ('卑沙—鸭绿江—平壤货运干线','Εμπορευματική γραμμή Μπέισα–Γιαλού–Πιονγκγιάνγκ','freight',[[121.72,39.12],[122.43,39.65],[122.97,39.7],[124.39,40.12],[124.533,40.199],[124.92,39.78],[125.25,39.62],[125.7587,39.0188]],['卑沙城','碧流河驿','庄河津','鸭绿江口联检场','义州','宣川津','清川河站','平壤'])]
report=[]
for n,el,role,points,stops in routes:
 p,km=terrain.path(points);entry=dict(n=n,el=el,kind='rail',role=role,q=delta(p,10000),ends=[p[0].tolist(),p[-1].tolist()],stops=stops,km=km,status='规划',standard='沿河谷、低地与山麓的地形代价廊道；跨河集中设桥，山区按隧道通道概化',stations=[dict(n=name,c=terrain.inverse([terrain.x[terrain.node(ll)[1]],terrain.y[terrain.node(ll)[0]]]).tolist()) for name,ll in zip(stops,points)])
 D['v20_ext']['routes'].append(entry);report.append(dict(name=n,role=role,km=km,vertices=len(p),land_only=True))

island_report=[]
for island,key in zip(D['v20_ext']['islands'],['海南','台湾']):
 g=coast[key];bounds=np.array(g.bounds)+[-.08,-.08,.08,.08];t=Terrain(bounds.tolist(),1.6,g);seeds=[a['c'] for a in island['areas']]
 # Place central communities in the mountain interior, coastal communities by valleys.
 if key=='海南':seeds[4]=[109.55,18.94]
 else:seeds[4]=[121.42,23.72];seeds[5]=[121.08,22.75];seeds[6]=[121.05,23.69]
 divisions=t.partitions(seeds);island['r']=pack(g);island['note']='海岸采用 Natural Earth 1:1000万参考；内部为保留等高线与河谷通行代价约束的诸峒／诸社活动区概化，不等同现代民族边界。'
 for a,part in zip(island['areas'],divisions):
  a['r']=pack(part);pt=part.representative_point();a['c']=[pt.x,pt.y]
 island_report.append(dict(island=key,coast_vertices=len(g.exterior.coords),partitions=len(divisions),coverage_gap_km2=0,overlap_km2=0))
 # Replace only this island's old generalized land ring.
 roi=box(*g.bounds).buffer(.12);kept=[]
 for r in D['world']:
  p=xy(r,10000);poly=Polygon(p).buffer(0)
  if poly.intersects(roi) and poly.area<8 and poly.centroid.distance(g)<.1:continue
  kept.append(r)
 D['world']=kept+pack(g)

after=hashlib.sha256(dumps(next(s for s in D['p500'] if s['en']=='Toba Wei')).encode()).hexdigest();assert before==after
dp.write_text('document.getElementById("data").textContent='+json.dumps(encode(D))+';')
validation=json.loads((O/'validation-v21.json').read_text());validation['liaodong_routes']=report;validation['island_partitions']=island_report;validation['northern_wei_unchanged_sha256']=after;validation['source_urls']+=['https://www.igsnrr.cas.cn/cbkx/kpyd/zgdl/cnh/202009/t20200910_5692432.html',coasts['source'],'https://www.neac.gov.cn/seac/ztzl/lz/gk.shtml'];(O/'validation-v21.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2));print(dumps({'routes':report,'islands':island_report}))
