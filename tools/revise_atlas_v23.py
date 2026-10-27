"""v23: city-specific land, water and terrain constrained fictional planning.
Historical place evidence and modern amenities are explicitly separate.
"""
from pathlib import Path
import json,pickle,copy,math,hashlib,heapq,time
import numpy as np,shapely
from shapely.geometry import Polygon,LineString,Point,box
from shapely.ops import unary_union,nearest_points,transform,substring
from scipy import ndimage
from scipy.spatial import cKDTree
from scipy.interpolate import CubicSpline
from pyproj import CRS,Transformer
from skimage.measure import find_contours
from revise_atlas_v20 import decode,encode,dumps,xy,delta,pack,polygons,area
R=Path(__file__).resolve().parents[1];O=R/'dist';T=R/'analysis-v23';T.mkdir(exist_ok=True)
if (T/'base.pkl').exists():D,A,files=pickle.load(open(T/'base.pkl','rb'))
else:
 D=decode(json.loads((O/'data/v22_d.js').read_text().split('=',1)[1].strip().rstrip(';')));A={};files={}
 for p in sorted((O/'data').glob('v21*.js')):
  if p.name=='v21_d.js':continue
  prefix,body=p.read_text().split('=',1);d=json.loads(body.strip().rstrip(';'));files[p.name]=(prefix,d);A.update(d)
 pickle.dump((D,A,files),open(T/'base.pkl','wb'))
C=decode(A['l_city.json']);PATCH=decode(A.get('city-patch.json',encode({})));OV=decode(A.get('city-overview-patch.json',encode({})))
for s in C['city']:
 if s['k'] in OV:s.update(OV[s['k']])
def poly(q,sc=20):
 a=xy(q,sc);return Polygon(a).buffer(0) if len(a)>2 else Polygon()
def geo(rs,sc=20):
 gs=[poly(r['r'],r.get('m') or sc) if isinstance(r,dict) else poly(r,sc) for r in rs];gs=[g for g in gs if not g.is_empty];return shapely.symmetric_difference_all(gs) if gs else Polygon()
def parts(g):return [x for x in shapely.get_parts(g) if x.geom_type=='LineString' and len(x.coords)>1]
def localrings(g):return [delta(r.coords) for p in polygons(g) for r in [p.exterior,*p.interiors]]
def cityrings(g):return [dict(r=delta(r.coords,1000),m=1000) for p in polygons(g) for r in [p.exterior,*p.interiors]]
def bake(c):
 p=PATCH.get(c['k'])
 if p and c.get('_urban_v14_applied')!='urban-v14-20261023':
  rem=set(p.get('road_remove_v14',[]));repl={r['i']:r['parts'] for r in p.get('road_replacements_v14',[])};c['road']=[rr for i,r in enumerate(c['road']) if i not in rem for rr in copy.deepcopy(repl.get(i,[r]))]+copy.deepcopy(p.get('road_add_v14',[]))
  for a in p.get('district_program_v14',[]):
   if a['i']<len(c['dist']):c['dist'][a['i']].update({k:v for k,v in a.items() if k!='i'})
  omit={'district_program_v14','road_remove_v14','road_replacements_v14','road_add_v14','road_width_defaults_v14','metro_xpkm_v14'};c.update(copy.deepcopy({k:v for k,v in p.items() if k not in omit}));c['xp']+=copy.deepcopy(c.get('external_airport_access_v14',[]))
 c['_urban_v14_applied']='urban-v14-20261023';return c
P=D['proj']
def project(ll):
 a=np.asarray(ll);lo=np.radians(a[...,0]);la=np.radians(a[...,1]);e=math.sqrt(P['E2']);ss=np.sin(la);q=(1-P['E2'])*(ss/(1-P['E2']*ss*ss)-np.log((1-e*ss)/(1+e*ss))/(2*e));rho=P['RA']*np.sqrt(P['C']-2*P['N']*q/P['QP'])/P['N'];th=P['N']*(lo-P['L0']);return np.stack([rho*np.sin(th)/1000,(P['RHO0']-rho*np.cos(th))/1000],axis=-1)
def unproject(a):
 a=np.asarray(a);x=a[...,0]*1000;y=a[...,1]*1000;e=math.sqrt(P['E2']);rho=np.hypot(x,P['RHO0']-y);th=np.arctan2(x,P['RHO0']-y);q=P['QP']*(P['C']-(rho*P['N']/P['RA'])**2)/(2*P['N']);la=np.arcsin(np.clip(q/P['QP'],-1,1))
 for _ in range(9):
  ss=np.sin(la);v=(1-P['E2'])*(ss/(1-P['E2']*ss*ss)-np.log((1-e*ss)/(1+e*ss))/(2*e));la+=(q-v)/(2*(1-P['E2'])*np.cos(la)/(1-P['E2']*ss*ss)**2)
 return np.stack([(th/P['N']+P['L0'])*180/np.pi,la*180/np.pi],axis=-1)
def transformer(c,inverse=False):
 t=c['lt'];crs=CRS.from_proj4(f"+proj=aeqd +lat_0={t['lat0']} +lon_0={t['lon0']} +R={t.get('R',6371008.8)} +units=m");return Transformer.from_crs(crs,'EPSG:4326',always_xy=True) if inverse else Transformer.from_crs('EPSG:4326',crs,always_xy=True)
def local(c,ll):
 a=np.asarray(ll)
 if c.get('lt',{}).get('kind')=='aeqd':x,y=transformer(c).transform(a[...,0],a[...,1]);p=np.stack([x/1000,y/1000],axis=-1)
 else:p=project(a)
 return np.stack([p[...,0]-c['o'][0],c['o'][1]-p[...,1]],axis=-1)
def world(c,a):
 a=np.asarray(a);p=np.stack([a[...,0]+c['o'][0],c['o'][1]-a[...,1]],axis=-1)
 if c.get('lt',{}).get('kind')=='aeqd':x,y=transformer(c,True).transform(p[...,0]*1000,p[...,1]*1000);return np.stack([x,y],axis=-1)
 return unproject(p)
class Plan:
 def __init__(self,c):
  self.c=c;self.w=c['w'];self.step=max(.16,min(.32,self.w/430));self.n=math.ceil(self.w/self.step)+1
  self.lake=unary_union([geo(c.get('lake',[])),*[poly(q) for q in c.get('terrain',{}).get('lakes',[])]])
  if c.get('xuanwu_v21'):self.lake=unary_union([self.lake,poly(c['xuanwu_v21']['r'])])
  self.water=unary_union([geo(c.get('sea',[])),self.lake]);self.land=box(.04,.04,self.w-.04,self.w-.04).difference(self.water.buffer(.045)).buffer(0)
  self.rivers=unary_union([LineString(xy(r['q'])).buffer(max(.025,r['w']/2+.025)) for r in c.get('riv',[]) if len(r.get('q',[]))>3]);self.buildable=self.land.difference(self.rivers.buffer(.025));self.safe=self.land.buffer(-.035);self.safe=self.safe if not self.safe.is_empty else self.land;self.ready_=False;self.memo={}
 def ready(self):
  if self.ready_:return
  self.ready_=True;v=np.arange(self.n)*self.step;xx,yy=np.meshgrid(v,v);self.mask=shapely.contains_xy(self.safe,xx,yy);self.cc,_=ndimage.label(self.mask,np.ones((3,3)));self.cells=np.column_stack(np.nonzero(self.mask));self.tree=cKDTree(self.cells[:,::-1]*self.step);self.cost=np.ones_like(xx)
  points=[];values=[]
  for ct in self.c.get('terrain',{}).get('contours',[]):
   a=xy(ct['q'])[::3];points.extend(a);values.extend([ct['e']]*len(a))
  if points:
   dist,idx=cKDTree(points).query(np.column_stack([xx.ravel(),yy.ravel()]));e=np.array(values)[idx].reshape(xx.shape);e=ndimage.gaussian_filter(e,1.2);gy,gx=np.gradient(e,self.step*1000);self.cost+=np.minimum(8,14*np.hypot(gx,gy))+np.maximum(0,e)/3500
  clear=ndimage.distance_transform_edt(self.mask)*self.step;self.cost+=.08/np.maximum(.08,clear)
 def snap(self,p,build=False):
  g=self.buildable.buffer(-.04) if build else self.safe
  if g.is_empty:g=self.land
  p=Point(p);return np.array(p.coords[0] if g.covers(p) else nearest_points(p,g)[1].coords[0])
 def path(self,a,b):
  a=self.snap(a);b=self.snap(b)
  if self.safe.covers(LineString([a,b])) and np.linalg.norm(b-a)<.45:return np.array([a,b])
  self.ready();_,ii=self.tree.query([a,b]);start=tuple(self.cells[ii[0]]);end=tuple(self.cells[ii[1]])
  if self.cc[start]!=self.cc[end]:return None
  key=(start,end)
  if key in self.memo:q=self.memo[key]
  else:
   queue=[(0,0,start)];cost={start:0};prev={};found=False
   while queue:
    _,g,u=heapq.heappop(queue)
    if g!=cost.get(u):continue
    if u==end:found=True;break
    for dy,dx in [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]:
     v=(u[0]+dy,u[1]+dx)
     if not(0<=v[0]<self.n and 0<=v[1]<self.n) or not self.mask[v]:continue
     if dx and dy and not(self.mask[u[0],v[1]] and self.mask[v[0],u[1]]):continue
     ng=g+math.hypot(dx,dy)*(self.cost[u]+self.cost[v])*.5
     if ng<cost.get(v,1e99):cost[v]=ng;prev[v]=u;heapq.heappush(queue,(ng+math.hypot(v[0]-end[0],v[1]-end[1]),ng,v))
   if not found:return None
   path=[end]
   while path[-1]!=start:path.append(prev[path[-1]])
   q=np.array(path[::-1])[:,::-1]*self.step;self.memo[key]=q
  q=np.vstack([a,q,b]);keep=[q[0]]
  # Remove raster stair steps locally, retaining terrain-driven corridor bends.
  i=1
  while i<len(q):
   j=min(len(q)-1,i+4)
   while j>i and not self.safe.covers(LineString([keep[-1],q[j]])):j-=1
   if not self.land.covers(LineString([keep[-1],q[j]])):return None
   keep.append(q[j]);i=j+1
  q=np.array(keep)
  for _ in range(2):
   if len(q)<3:break
   out=[q[0]]
   for i in range(1,len(q)-1):
    p=q[i];u=p*.78+q[i-1]*.22;v=p*.78+q[i+1]*.22
    if self.safe.covers(LineString([out[-1],u,v,q[i+1]])):out.extend([u,v])
    else:out.append(p)
   out.append(q[-1]);q=np.array(out)
  return q
 def roads(self,roads):
  out=[];fix=0
  for r in roads:
   if len(r.get('q',[]))<4:continue
   arr=xy(r['q']);g=LineString(arr)
   if self.land.covers(g):out.append(r);continue
   fix+=1;pieces=parts(g.intersection(self.safe));pieces=sorted(pieces,key=lambda x:g.project(Point(x.coords[0])))
   merged=[]
   for piece in pieces:
    a=np.array(piece.coords)
    if len(a)<2 or piece.length<.025:continue
    if merged:
     conn=self.path(merged[-1][-1],a[0])
     if conn is not None:merged[-1]=np.vstack([merged[-1],conn[1:],a[1:]]);continue
    merged.append(a)
   for i,a in enumerate(merged):
    rr=copy.deepcopy(r);rr['q']=delta(a);rr['ring']=0;rr.pop('el',None)
    if 'lab' in rr:rr['lab']=np.mean(a,axis=0).round(3).tolist()
    if len(merged)>1 and rr.get('n'):rr['n']=rr['n'].replace('绕城','沿岸').replace('环城','沿岸')+(' · 西岸' if i==0 else ' · 东岸' if i==1 else ' · 陆域段')
    rr['planning_v23']='陆域与地形通道约束；水域分隔时保留开放沿岸段';out.append(rr)
  return out,fix
 def metro(self):
  c=self.c;moved=0;fixed=0;split=0
  for n in c['mn']:
   p=np.array(n['c'])/20
   if not self.land.covers(Point(p)):n['c']=(self.snap(p)*20).round(3).tolist();moved+=1
  for l in c['ml']:
   arr=xy(l['q']);g=LineString(arr)
   if self.land.covers(g):continue
   fixed+=1;nd=l.get('nd',[]);points=[np.array(c['mn'][i]['c'])/20 for i in nd]
   if len(points)<2:points=[self.snap(arr[0]),self.snap(arr[-1])]
   # Keep original subalignment whenever it stays on land and shared stops match.
   seq=[];chains=[]
   for a,b in zip(points,points[1:]):
    ta=g.project(Point(a));tb=g.project(Point(b));sub=substring(g,ta,tb)
    if sub.geom_type=='LineString':raw=np.vstack([a,np.array(sub.coords),b])
    else:raw=np.array([a,b])
    q=raw if self.land.covers(LineString(raw)) else self.path(a,b)
    if q is None:
     if len(seq)>1:chains.append(np.array(seq));seq=[]
     continue
    seq.extend(q if not seq else q[1:])
   if len(seq)>1:chains.append(np.array(seq))
   if chains:
    l['q']=delta(chains[0]);l['km']=round(sum(LineString(q).length for q in chains),3);l['ring']=0
    if len(chains)>1:l['v23_parts']=[delta(q) for q in chains];split+=1
   else:
    cut=parts(g.intersection(self.safe));l['v23_parts']=[delta(q.coords) for q in cut];l['q']=l['v23_parts'][0] if cut else [];split+=1
   l['xr']=[];l['alignment_v23']='沿当地高程、湖岸与陆域重选走廊；岛屿间未落实跨海工程的部分分段显示'
  return moved,fixed,split
DE='Dieser Atlas entwirft eine alternative Welt mit dem Zeithorizont 497. Historische Ortsnamen und belegte Erinnerungsorte geben den Städten ihre Grundlage. Moderne Bahnnetze, Flughäfen, Wohnquartiere und Werkstätten für dreidimensionalen Druck gehören zur erfundenen Entwicklung. Flüsse, Küsten und Berge bestimmen Verkehrswege und Quartiere. Besondere Freistädte verbinden Handel, Forschung und gemeinschaftliche Gestaltung. Ausschließliche Wirtschaftszonen und Linienarten erläutert die Kartenlegende.'
EL='Ο άτλαντας παρουσιάζει έναν εναλλακτικό κόσμο με χρονικό ορίζοντα το έτος 497. Τα ιστορικά τοπωνύμια και οι τεκμηριωμένοι τόποι μνήμης δίνουν στις πόλεις τον χαρακτήρα τους. Τα σύγχρονα σιδηροδρομικά δίκτυα, τα αεροδρόμια, οι κατοικίες και τα εργαστήρια τρισδιάστατης εκτύπωσης ανήκουν στη φανταστική εξέλιξη του κόσμου. Ακτές, ποταμοί και βουνά καθοδηγούν τον σχεδιασμό. Οι ειδικές ελεύθερες πόλεις συνδέουν εμπόριο, έρευνα και δημιουργία. Η Αποκλειστική Οικονομική Ζώνη (ΑΟΖ) εξηγείται στο υπόμνημα.'
def civic(c,p,s):
 seed=int.from_bytes(hashlib.sha256(c['k'].encode()).digest()[:4],'little');nodes=[np.array(n['c'])/20 for n in c['mn']];core=np.mean(nodes,axis=0) if nodes else np.array([c['w']/2]*2);candidates=[np.array(d['c'])/20 for d in c['dist']]+nodes[::max(1,len(nodes)//50)];used=[];el=s.get('el') or c.get('el') or s.get('lat_name') or c['n']
 def choose(t,green=False):
  land=p.land if green else p.buildable;safe=land.buffer(-.1);safe=safe if not safe.is_empty else land
  for q in sorted(candidates,key=lambda q:np.linalg.norm(t-q)):
   if safe.covers(Point(q)) and all(np.linalg.norm(q-r)>.4 for r in used):used.append(q);return q
  q=np.array(nearest_points(Point(t),safe)[1].coords[0]);used.append(q);return q
 cats=[('shopping','综合商场','Εμπορικό κέντρο',['购物','餐厅','影院']),('restaurant','街区餐厅','Εστιατόρια γειτονιάς',['餐饮','步行街']),('cinema','影院与演艺中心','Κινηματογράφος',['电影','演艺']),('makerspace','创作工坊','Εργαστήριο δημιουργίας',['设计','修复','创作']),('fabrication','三维打印与数字制造园','Τρισδιάστατη εκτύπωση',['3D打印','数字制造']),('park','市民公园','Αστικό πάρκο',['城市公园','运动']),('suburban_park','郊野生态公园','Περιαστικό πάρκο',['郊野公园','山林步道']),('river_district','河流特别区','Παραποτάμια ειδική ζώνη',['河岸修复','防洪绿地','公共滨水'])];out=[]
 for i,(kind,n,gr,services) in enumerate(cats):
  target=core+np.array([math.cos(i*2.4),math.sin(i*2.4)])*min(c['w']*.22,3+i*.8)
  if kind=='shopping':target=core
  if kind=='suburban_park':target=core+np.array([.7,-.7])*c['w']*.28
  if kind=='river_district' and c['riv']:target=np.array(LineString(xy(max(c['riv'],key=lambda r:len(r['q']))['q'])).interpolate(.5,normalized=True).coords[0])
  green=kind in ['park','suburban_park','river_district'];q=choose(target,green)
  if green:g=Point(q).buffer(.7 if kind=='park' else 1.5,quad_segs=14).intersection(p.land)
  else:g=Polygon([(q[0]-.14,q[1]-.10),(q[0]+.14,q[1]-.10),(q[0]+.14,q[1]+.10),(q[0]+.04,q[1]+.10),(q[0]+.04,q[1]+.03),(q[0]-.14,q[1]+.03)]).intersection(p.buildable)
  if kind=='river_district' and c['riv']:g=LineString(xy(max(c['riv'],key=lambda r:len(r['q']))['q'])).buffer(.32).intersection(Point(q).buffer(4)).intersection(p.land)
  out.append(dict(n=c['n']+' · '+n,el=str(el)+' · '+gr,kind=kind,c=(q*20).round(3).tolist(),r=localrings(g),services=services,status='架空规划',basis='依本城海陆、水系、地形、轨道节点与街区选择设施位置；非现实商户名录'))
 h=c.get('historical_name',{});q=choose(np.array(c['dist'][0]['c'])/20 if c['dist'] else core,True);out.insert(0,dict(n=(c.get('hist') or h.get('display') or c['n'])+' · 史载城址参照',el=str(el)+' · ιστορικός πυρήνας',kind='historic_site',c=(q*20).round(3).tolist(),r=[],services=['历史地标','城址历史'],status='史载名称／城址参照',period=h.get('period','约497年城市参照'),sources=h.get('sources',[]),basis=h.get('note','古城名称、城址有文献依据；位置概化，不推定现存古建筑轮廓')))
 for a in RESEARCH:
  if a['city_key']==c['k']:
   q=local(c,a['c'])
   if np.all(q>=0) and np.all(q<=c['w']):out.insert(0,{**a,'c':(q*20).round(3).tolist(),'r':[],'services':['历史地标','考古与城市记忆'],'kind':'historic_site'})
 c['amenities_v23']=out;c['planning_v23']=dict(city_seed=seed,coast_fraction=round(1-p.land.area/c['w']**2,3),urban_form='滨水与港湾组团' if p.water.area/c['w']**2>.12 else '河谷与山麓组团' if c['riv'] else '平原交通节点组团',land_r=localrings(p.land),facilities='现代设施为架空规划；史载地标附独立年代与来源')
 major=[LineString(xy(r['q'])) for r in c['road'] if r.get('k') in [1,2] and len(r.get('q',[]))>3]
 for i,d in enumerate(c['dist']):
  q=np.array(d['c'])/20;g=geo(d['r']).intersection(p.land)
  if not g.is_empty:d['r']=cityrings(g);d['c']=(np.array(g.representative_point().coords[0])*20).round(3).tolist();d['a']=round(g.area,3)
  if major:
   road=min(major,key=lambda r:r.distance(Point(q)));t=road.project(Point(q));a=road.interpolate(max(0,t-.2));b=road.interpolate(min(road.length,t+.2));d['ang']=round(math.degrees(math.atan2(b.y-a.y,b.x-a.x)),1)
  d['sp']=int(160+(seed+i*43)%160);d['pat']='organic' if i==0 else 'curvi' if p.water.distance(Point(q))<1.5 else 'grid'
 for d in c.get('special_districts',[]):
  g=geo(d.get('r',[]),d.get('scale',1000)).intersection(p.land)
  if not g.is_empty:d['r']=cityrings(g);d['scale']=1000;d['c']=list(g.representative_point().coords[0]);d['area_km2']=round(g.area,3)
 for d in c.get('planning_areas_v14',[]):
  if d.get('c') and not p.land.covers(Point(np.array(d['c'])/20)):d['c']=(p.snap(np.array(d['c'])/20)*20).round(3).tolist()
def jinan(c,p,s):
 c['n']='晋安（侯官）';c['historical_name']['display']='晋安郡城 · 侯官';c['historical_name']['aliases']+=['晋安','晋安郡城'];c['historical_name']['sources'].append(dict(title='福州市政府：严高营建子城与东西湖',url='https://www.fuzhou.gov.cn/zgfzzt/zjrc/mdfc/mdrj/201811/t20181112_2674287.htm'))
 for name,col,wps,names in [('晋安子城线','#b94d43',[[119.285,26.112],[119.297,26.104],[119.298,26.09],[119.291,26.076],[119.307,26.054]],['西湖西津','冶山','晋安子城','乌山北麓','台江北岸']),('闽江北岸线','#2d7f8d',[[119.241,26.066],[119.289,26.059],[119.324,26.046],[119.368,26.044],[119.403,26.039]],['金山渡北','台江上游','鳌峰津','鼓山河口','东津港'])]:
  way=[p.snap(q) for q in local(c,wps)];arr=[]
  for a,b in zip(way,way[1:]):
   q=p.path(a,b);assert q is not None,name;arr.extend(q if not arr else q[1:])
  line=LineString(arr);nst=max(8,round(line.length/.95)+1);nd=[]
  for i,t in enumerate(np.linspace(0,1,nst)):
   q=np.array(line.interpolate(t,normalized=True).coords[0]);n=names[min(len(names)-1,round(t*(len(names)-1)))]+('' if i in [0,nst-1] else ['东里','南坊','西坊','北里','学舍','驿前','市廛'][i%7]);nd.append(len(c['mn']));c['mn'].append(dict(n=n,c=(q*20).round(3).tolist(),l=[len(c['ml'])],s=((q-c['w']/2)*2).round(3).tolist()))
  c['ml'].append(dict(n=name,col=col,k='line',s='规划',ring=0,km=round(line.length,3),q=delta(line.coords),nd=nd,op=0,xr=[],alignment_v23='晋安子城、西湖、乌山与闽江北岸独立地形走廊'));c['metro']['nl']+=1;c['metro']['nst']+=nst;c['metro']['kmp']+=line.length;c['metro']['total_km']=c['metro'].get('total_km',0)+line.length
 s['n']=c['n'];s['historical_name']=c['historical_name']
def northeast():
 gog=next(s for s in D['p500'] if s['en']=='Koguryo');wei=next(s for s in D['p500'] if s['en']=='Toba Wei');old=geo(gog.get('fb') or gog['r'],10000)
 anchor=np.array([[119.80,40],[119.83,40.35],[119.76,40.95],[119.65,41.55],[119.9,42.05],[120.22,42.55],[120.1,43.15],[120.65,43.85],[121.35,44.35],[122.15,44.65],[123.1,44.65],[124.15,44.7],[125.25,44.55],[126.4,44.4],[127.55,44.2],[128.75,44.25],[130,44.25],[131.35,43.95],[132,43.55]])
 ts=np.r_[0,np.cumsum(np.linalg.norm(np.diff(anchor,axis=0)*[.75,1],axis=1))];t=np.linspace(0,ts[-1],int(ts[-1]/.012)+1);a=CubicSpline(ts,anchor,axis=0,bc_type='natural')(t);v=np.gradient(a,axis=0);n=np.column_stack([-v[:,1],v[:,0]]);n/=np.linalg.norm(n,axis=1)[:,None];rng=np.random.default_rng(49723);noise=np.zeros(len(t))
 for scale,amp in [(1.1,.035),(.36,.018),(.12,.008),(.035,.003)]:knots=np.arange(0,ts[-1]+scale,scale);noise+=np.interp(t,knots,rng.normal(0,amp,len(knots)))
 a+=n*noise[:,None]*np.sin(np.linspace(0,np.pi,len(t)))[:,None];roi=box(118.7,37,134,46);land=unary_union([poly(q,10000).intersection(roi) for q in D['world'] if len(q)>5 and poly(q,10000).intersects(roi)]);cap=Polygon(np.vstack([a,[134,43.4],[134,35],[119,35],a[0]]));added=cap.intersection(land).intersection(box(118.7,38.6,134,46));new=shapely.set_precision(unary_union([old,added]).buffer(0),.0001)
 gog.update(r=pack(new),fb=pack(new),a=area(new),asph=area(new),a2=area(new));gog['intro']+=' v23架空设定：龙城、扶余与辽东全境归高句丽，西邻北魏，设两侧缓冲带。'
 for b in gog.get('bands',[]):
  g=unary_union([geo(b.get('f') or b['r'],10000),added.buffer(-max(0,b['t']-.06)*.14)]).intersection(new);b['r']=pack(g);b['f']=b['r']
 for s in D['p500']:
  if s is gog:continue
  for k in ['r','fb','wc','wl','ts']:
   if s.get(k):s[k]=pack(shapely.difference(geo(s[k],10000),new,grid_size=.0001))
  for b in s.get('bands',[]):
   for k in ['r','f']:
    if b.get(k):b[k]=pack(shapely.difference(geo(b[k],10000),new,grid_size=.0001))
 for group in ['xian','jun','zhou']:
  for s in D['wei17'].get(group,[]):
   if s.get('r'):s['r']=pack(shapely.difference(geo(s['r'],10000),new,grid_size=.0001))
  D['wei17'][group]=[s for s in D['wei17'].get(group,[]) if s.get('r')]
 # Resolve quantized border junctions at sub-centimetre precision on the Wei side.
 new=geo(gog['r'],10000);wg=geo(wei['r'],10000).difference(new);wei['r']=[np.diff(np.round(np.asarray(r.coords)*10000,6),axis=0,prepend=[[0,0]]).round(6).ravel().tolist() for p in polygons(wg) for r in [p.exterior,*p.interiors]];wei['a']=area(wg)
 if wei.get('wnom'):wei['wnom'].update(aT=wei['a'],aC=area(geo(wei.get('wc',[]),10000)),aL=area(geo(wei.get('wl',[]),10000)),version='v23 fictional NE frontier',note='龙城、扶余、辽东归高句丽；北魏与高句丽直接接壤。')
 if D['L'].get('weiline'):D['L']['weiline']=[delta(p.coords,10000) for q in D['L']['weiline'] for p in parts(LineString(xy(q,10000)).difference(new))]
 shared=new.boundary.intersection(wg.boundary);near=new.boundary.intersection(wg.buffer(.00015));buffer=near.buffer(.12).intersection(land)
 for name,ll in [('龙城',[120.4508,41.5801]),('扶余',[124.85,43.45]),('辽东城',[123.1727,41.2578]),('卑沙城',[121.95,39.15])]:assert new.covers(Point(ll)),name
 for state in D['p500']:
  if state is gog:continue
  moved=[c for c in state.get('cities',[]) if c.get('lon') is not None and new.covers(Point(c['lon'],c['lat']))]
  state['cities']=[c for c in state.get('cities',[]) if c not in moved];gog['cities'].extend(moved)
 gog['cities'].append(dict(n='龙城（和龙）',lon=120.4508,lat=41.5801,w=1));return dict(frontier=delta(a,10000),buffer_r=pack(buffer),buffer_el='Ζώνη μεθοριακής αποστρατιωτικοποίησης',buffer_zh='北魏—高句丽边境缓冲区',buffer_width_km='约20—25公里，两侧展开',shared_border_deg=shared.length,basis='依辽西山地、大兴安岭东麓与松辽平原过渡带概化的架空疆界；非497年史实复原')
def smooth(island):
 land=geo(island['r'],10000);areas=island['areas'];x0,y0,x1,y1=land.bounds;step=.0025;xs=np.arange(x0-step,x1+step*2,step);ys=np.arange(y0-step,y1+step*2,step);xx,yy=np.meshgrid(xs,ys);mask=shapely.contains_xy(land,xx,yy);fields=[]
 for a in areas:fields.append(ndimage.gaussian_filter(shapely.contains_xy(geo(a['r'],10000),xx,yy).astype(float),3.5))
 labels=np.argmax(np.stack(fields),axis=0);taken=Polygon();out=[]
 for i,a in enumerate(areas):
  rings=[]
  for q in find_contours(np.pad((labels==i)&mask,1).astype(float),.5):
   if len(q)>3:rings.append(Polygon(np.column_stack([x0-step+(q[:,1]-1)*step,y0-step+(q[:,0]-1)*step])).buffer(0))
  g=shapely.symmetric_difference_all(rings).intersection(land).difference(taken) if rings else Polygon();out.append(g);taken=unary_union([taken,g])
 gaps=land.difference(taken)
 for g in polygons(gaps):
  if not g.is_empty:i=min(range(len(out)),key=lambda i:out[i].distance(g.representative_point()));out[i]=unary_union([out[i],g])
 out=list(shapely.coverage_simplify(np.array(out,dtype=object),.0016,simplify_boundary=False))
 for a,g in zip(areas,out):a['r']=[np.diff(np.round(np.asarray(r.coords)*10000,6),axis=0,prepend=[[0,0]]).round(6).ravel().tolist() for p in polygons(g) for r in [p.exterior,*p.interiors]];a['c']=list(g.representative_point().coords[0])
 return dict(name=island.get('n'),gap_degrees2=land.symmetric_difference(unary_union(out)).area,overlap_degrees2=sum(g.area for g in out)-unary_union(out).area,method='shared smooth membership boundary; detailed coast retained')
RESEARCH=json.loads((R/'tools/landmarks-research-v23.json').read_text())['landmarks']
def build():
 cities={};reports=[];start=time.time()
 for ix,s in enumerate(C['city']):
  key='c/'+s['k']+'.json'
  if key not in A:continue
  c=bake(decode(A[key]));p=Plan(c);c['road'],rf=p.roads(c['road']);c['expwy'],ef=p.roads(c.get('expwy',[]));sm,mf,sp=p.metro()
  if c['k']=='q0065':jinan(c,p,s)
  civic(c,p,s)
  if c['k']=='wdf268c':c['st']='高句丽';s['st']='高句丽';s['pol']='Koguryo';c['nom']='v23架空疆界：龙城（和龙）归高句丽'
  c['planning_v23'].update(roads_repaired=rf,expressways_repaired=ef,metro_stations_shifted=sm,metro_lines_repaired=mf,sea_crossing_studies=sp)
  s['ml']=[dict(n=l['n'],col=l['col'],s=l['s'],q=delta(world(c,xy(q)),10000)) for l in c['ml'] for q in l.get('v23_parts',[l['q']]) if len(q)>3];s['ms']=[dict(n=n['n'],c=world(c,np.array(n['c'])/20).round(7).tolist(),i=len(n['l'])>1,w=4 if len(n['l'])>1 else 1) for n in c['mn']];s['nl']=c['metro']['nl'];s['amenities23']=[{k:v for k,v in a.items() if k not in ['r','c']} for a in c['amenities_v23']]
  if c['k']=='q0000':
   lake=transform(lambda x,y,z=None:tuple(world(c,np.column_stack([x,y])).T),p.lake)
   for k in ['sub','metro']:
    if D['L'].get(k) and isinstance(D['L'][k],list) and (not D['L'][k] or isinstance(D['L'][k][0],list)):D['L'][k]=[delta(g.coords,10000) for q in D['L'][k] for g in parts(LineString(xy(q,10000)).difference(lake))]
  A[key]=encode(c);cities[c['k']]=c;reports.append(dict(city=c['k'],name=c['n'],**{k:v for k,v in c['planning_v23'].items() if k!='land_r'}))
  if ix%20==0:print(ix+1,'/',len(C['city']),c['n'],'roads',rf,ef,'metro',mf,'seconds',round(time.time()-start),flush=True)
 D['c20']['nst']=sum(len(c['mn']) for c in cities.values());frontier=northeast();islands=[smooth(i) for i in D['v20_ext']['islands']];D['v23']=dict(frontier=frontier,island_borders=islands,city_count=len(cities),worldview=dict(de=DE,el=EL));A['l_city.json']=encode(C);A['city-patch.json']=encode({});A['city-overview-patch.json']=encode({})
 for l in D['v20_ext']['routes']:
  if l['kind']=='bridge':l['col']='#c77b30' if '西桥' in l['n'] else '#267bb8';l['el']='Δυτική γέφυρα του Τσιονγκτζόου' if '西桥' in l['n'] else 'Ανατολική γέφυρα του Τσιονγκτζόου'
 for name,(prefix,d) in files.items():
  for k in d:
   if k in A:d[k]=A[k]
  (O/'data'/name.replace('v21_','v23_')).write_text(prefix+'='+dumps(d)+';')
 (O/'data/v23_d.js').write_text('document.getElementById("data").textContent='+json.dumps(encode(D))+';');(O/'planning-v23.json').write_text(json.dumps(dict(revision='v23',cities=reports,frontier={k:v for k,v in frontier.items() if k not in ['frontier','buffer_r']},islands=islands),ensure_ascii=False,indent=2));pickle.dump(cities,open(T/'cities.pkl','wb'));print('Completed',len(cities),'city-specific plans',flush=True)
if __name__=='__main__':build()
