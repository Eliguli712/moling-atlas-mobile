"""v24: restore exact v22 NE boundaries and rebuild conservative local transit.
Physical references constrain fictional planning; no engineering feasibility is claimed.
"""
from atlas24_support import *
import numpy as np, math, io, hashlib, time
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request,urlopen
from urllib.parse import urlencode
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
from skimage.measure import find_contours
import shapely
from shapely.geometry import LineString,Point,Polygon,box
from shapely.ops import unary_union,transform
D,A,FILES,C=baseline();N=planning_namespace(D);globals().update({k:N[k] for k in ['xy','delta','geo','poly','parts','polygons','cityrings','localrings','local','world','Plan']})
CACHE=R/'tools/terrain-v24';CACHE.mkdir(exist_ok=True);TILES=T/'tiles';TILES.mkdir(exist_ok=True)
SPECS={
'qv20_zhuyai':[('metro','珠崖城府线','#226d8b',[[110.296,19.943],[110.32,19.956],[110.35,19.957],[110.377,19.974],[110.395,19.982]],['城西','府城','南渡江西岸','东山麓'])],
'qv20_daner':[('lrt','儋耳田园轻轨','#4a8a65',[[109.323,19.493],[109.34,19.509],[109.36,19.517],[109.377,19.531],[109.385,19.549]],['西田','儋耳城','那大北坊','北山麓'])],
'qv20_qiongdong':[('lrt','琼东万泉轻轨','#2b8c9a',[[110.442,19.212],[110.461,19.223],[110.47,19.243],[110.49,19.254],[110.506,19.262]],['万泉南岸','嘉积','东岸市集','北津'])],
'qv20_lingshui':[('lrt','陵水滨河轻轨','#807440',[[109.999,18.475],[110.019,18.487],[110.035,18.498],[110.045,18.52],[110.052,18.532]],['南田','陵水城','滨河东坊','北城'])],
'qv20_danshui':[('metro','淡水山麓线','#226d8b',[[121.426,25.169],[121.437,25.166],[121.452,25.156],[121.462,25.14],[121.474,25.123]],['淡水津','城东','竹围','关渡北岸']),('lrt','淡海聚落轻轨','#4a8a65',[[121.432,25.176],[121.431,25.185],[121.435,25.194],[121.446,25.196],[121.451,25.19]],['海口','淡海新坊','北郊','山脚'])],
'qv20_dadu':[('lrt','大肚平原轻轨','#6a8b44',[[120.526,24.136],[120.532,24.149],[120.535,24.162],[120.541,24.177],[120.543,24.184]],['南平原','大肚津','北市','台地西麓'])],
'qv20_taijiang':[('metro','台江城港线','#2a7b8b',[[120.17,22.994],[120.181,23.009],[120.197,23.017],[120.214,23.023],[120.226,23.04]],['安平津','城西','台江城','北城'])],
'qv20_lanyang':[('lrt','兰阳平原轻轨','#367c5e',[[121.745,24.656],[121.758,24.671],[121.77,24.684],[121.786,24.702],[121.793,24.714]],['兰阳南坊','平原城','北市','河口西岸'])],
'qv20_hualien':[('lrt','洄澜河谷轻轨','#397b89',[[121.579,23.965],[121.585,23.98],[121.596,23.994],[121.606,24.01],[121.604,24.023]],['南坊','洄澜津','北城','河谷口'])],
'qv20_beinan':[('lrt','卑南平原轻轨','#7c8851',[[121.112,22.746],[121.12,22.76],[121.126,22.776],[121.133,22.791],[121.132,22.805]],['南平原','卑南津','东麓聚落','北津'])],
'q0065':[('metro','晋安东山—鼓山山麓线','#a34f85',[[119.309,26.132],[119.319,26.119],[119.337,26.098],[119.344,26.083],[119.35,26.065]],['东山','鹤林','晋安东城','鼓山西麓']),('metro','晋安北站接驳支线','#307f90',[[119.319,26.119],[119.322,26.108],[119.309,26.101],[119.295,26.096],[119.287,26.087]],['北站','斗门','冶山','西湖东津'])]}
cityBy={s['k']:s for s in C['city']};cities={k:decode(A['c/'+k+'.json']) for k in SPECS}
def download_tile(t):
 z,x,y=t;p=TILES/f'{z}-{x}-{y}.png'
 if not p.exists():
  with urlopen(f'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png',timeout=40) as r:p.write_bytes(r.read())
 a=np.asarray(Image.open(p).convert('RGB'),dtype=float);return t,a[:,:,0]*256+a[:,:,1]+a[:,:,2]/256-32768

def terrain(c):
 p=CACHE/(c['k']+'.npz')
 if p.exists():z=np.load(p);return z['dem'].astype(float),float(z['step'])
 step=.18;n=math.ceil(c['w']/step)+1;xx,yy=np.meshgrid(np.arange(n)*step,np.arange(n)*step);ll=world(c,np.stack([xx,yy],axis=-1));z=11;tx=(ll[:,:,0]+180)/360*2**z;ty=(1-np.arcsinh(np.tan(np.radians(ll[:,:,1])))/np.pi)/2*2**z;keys=[(z,x,y) for x,y in set(zip(np.floor(tx).astype(int).ravel(),np.floor(ty).astype(int).ravel()))];dem=np.zeros_like(tx)
 with ThreadPoolExecutor(max_workers=4) as pool:tiles=dict(pool.map(download_tile,keys))
 for (_,x,y),v in tiles.items():
  mask=(np.floor(tx)==x)&(np.floor(ty)==y);dem[mask]=ndimage.map_coordinates(v,[(ty[mask]-y)*255,(tx[mask]-x)*255],order=1,mode='nearest')
 np.savez_compressed(p,dem=dem.astype('float32'),step=step,source='Mapzen Terrain Tiles / Terrarium / z11 / 2026-10-27');return dem,step

def osm(region):
 p=R/'tools'/('references-v24-'+region+'.json.gz')
 if p.exists():return json.loads(gzip.decompress(p.read_bytes()))
 keys=[k for k in SPECS if k.startswith('qv20_') and ((k in ['qv20_zhuyai','qv20_daner','qv20_qiongdong','qv20_lingshui'])==(region=='hainan'))];queries=[]
 for k in keys:
  c=cities[k];ll=world(c,[[0,0],[c['w'],0],[0,c['w']],[c['w'],c['w']]]);lo,la=ll.min(axis=0);hi,up=ll.max(axis=0);b=f'({la:.5f},{lo:.5f},{up:.5f},{hi:.5f})'
  queries.extend(['way["highway"~"^(motorway|trunk|primary|secondary)$"]'+b+';','way["waterway"="river"]'+b+';'])
 q='[out:json][timeout:55];('+''.join(queries)+');out geom;'
 try:
  req=Request('https://overpass-api.de/api/interpreter',data=urlencode({'data':q}).encode(),headers={'User-Agent':'MolingAtlas-planning/24'})
  with urlopen(req,timeout=70) as r:d=json.load(r)
  p.write_bytes(gzip.compress(json.dumps(d,separators=(',',':')).encode(),mtime=0));print('OSM',region,len(d['elements']),flush=True);return d
 except Exception as e:print('OSM unavailable',region,type(e).__name__,flush=True);return {'elements':[]}

def prep_reference(c,dem,step,reference):
 if c['k']!='q0065':
  island=D['v20_ext']['islands'][0 if c['k'] in ['qv20_zhuyai','qv20_daner','qv20_qiongdong','qv20_lingshui'] else 1];g=geo(island['r'],10000)
  land=transform(lambda x,y,z=None:tuple(local(c,np.column_stack([x,y])).T),g).intersection(box(0,0,c['w'],c['w']));c['sea']=cityrings(box(0,0,c['w'],c['w']).difference(land));c['lake']=[];c['road']=[];c['expwy']=[];c['riv']=[]
  bounds=box(0,0,c['w'],c['w']);seen=set()
  features=[{'geometry':f['geometry']['coordinates'],'tags':{'highway':'primary','name':f['properties']['name']},'id':'v22-'+str(i)} for i,f in enumerate(json.loads((R/'tools/corridors-v22.geojson').read_text())['features'])]
  features += [e for e in reference['elements'] if e.get('geometry')]
  for e in features:
   raw=e['geometry'];ll=np.array([[v['lon'],v['lat']] for v in raw]) if isinstance(raw[0],dict) else np.array(raw);q=local(c,ll)
   if len(q)<2:continue
   line=LineString(q)
   if not line.intersects(bounds):continue
   tags=e.get('tags',{});wet=tags.get('waterway')=='river'
   for piece in parts(line.intersection(bounds).intersection(land.buffer(0 if wet else -.025))):
    if piece.length<.15:continue
    arr=np.array(piece.simplify(.008).coords);key=delta(arr)
    if str(key) in seen:continue
    seen.add(str(key))
    if wet:c['riv'].append({'q':key,'w':.055,'n':tags.get('name','河流')})
    else:c['road'].append({'q':key,'k':1 if tags.get('highway') in ['motorway','trunk'] else 2,'n':tags.get('name','参考干道'),'ring':0,'width_m':26,'axis':0,'reference_v24':'OSM or retained v22 road corridor'})
  # Remove synthetic rings, use real road geometry only in these city models.
  c['bridge']=[]
 contours=[]
 for e in [20,50,100,200,300,500,750,1000,1500,2000]:
  for q in find_contours(dem,float(e)):
   if len(q)<10:continue
   line=LineString(q[:,::-1]*step).simplify(.03)
   if line.length>.6:contours.append({'e':e,'q':delta(line.coords)})
 c['terrain']={'source':'https://registry.opendata.aws/terrain-tiles/','accessed':'2026-10-27','cell_km':step,'contours':contours,'lakes':c.get('terrain',{}).get('lakes',[]),'hill_names':c.get('terrain',{}).get('hill_names',[]),'crossings':[]}
 # Clip old urban envelopes and facilities to the same land mask.
 p=Plan(c);c.setdefault('planning_v23',{})['land_r']=localrings(p.land)
 for zone in c.get('zones',[]):zone['r']=cityrings(geo(zone['r']).intersection(p.land))
 for k in ['u','s','p','x']:
  if k in c['edge']:c['edge'][k]=cityrings(geo(c['edge'][k]).intersection(p.land))
 for d in c.get('dist',[]):
  gg=geo(d['r']).intersection(p.land)
  if not gg.is_empty:d['r']=cityrings(gg);d['a']=round(gg.area,3);d['c']=(np.array(gg.representative_point().coords[0])*20).round(3).tolist()
 for a in c.get('amenities_v23',[]):
  if a.get('c') and not p.land.covers(Point(np.array(a['c'])/20)):a['c']=(p.snap(np.array(a['c'])/20,build=True)*20).round(3).tolist()
  if a.get('r'):a['r']=localrings(geo(a['r']).intersection(p.land))
 return p

class TerrainPlan24(Plan):
 def __init__(self,c,dem,step):super().__init__(c);self.dem24=dem;self.cell24=step
 def ready(self):
  if self.ready_:return
  super().ready();xx,yy=np.meshgrid(np.arange(self.n)*self.step,np.arange(self.n)*self.step);e=ndimage.map_coordinates(self.dem24,[yy/self.cell24,xx/self.cell24],order=1,mode='nearest');e=ndimage.gaussian_filter(e,.6);gy,gx=np.gradient(e,self.step*1000);slope=np.degrees(np.arctan(np.hypot(gx,gy)));floor=ndimage.percentile_filter(e,20,size=9);relief=np.maximum(0,e-floor)
  self.mask &= (slope<(4 if getattr(self,'mode24','metro')=='lrt' else 10))&(e<(170 if self.c['k']=='q0065' else 250));self.cc,n=ndimage.label(self.mask,np.ones((3,3)));self.cells=np.column_stack(np.nonzero(self.mask));self.tree=cKDTree(self.cells[:,::-1]*self.step);self.cost=1+(slope/4)**2+np.minimum(10,relief/45)+np.maximum(0,e)/1500
  roadpts=[]
  for r in self.c['road']:
   if len(r.get('q',[]))<4:continue
   l=LineString(xy(r['q']));roadpts.extend(l.interpolate(float(t)).coords[0] for t in np.arange(0,l.length,.15))
  if roadpts:
   ds,_=cKDTree(roadpts).query(np.column_stack([xx.ravel(),yy.ravel()]));self.cost+=np.minimum(3,ds.reshape(xx.shape)*.9)
  if self.c['riv']:
   wet=shapely.contains_xy(self.rivers,xx,yy);self.cost+=np.where(wet,18,0)

reports=[];validation=[]
def add_line(c,p,mode,name,col,wps,names):
 p.mode24=mode;p.ready();arr=[];anchors=[]
 for q in local(c,wps):
  _,idx=p.tree.query(q);anchors.append(p.tree.data[idx])
 # Keep one connected lowland corridor and reject inaccessible remote anchors.
 tags=[p.cc[tuple(p.cells[p.tree.query(q)[1]])] for q in anchors];tag=max(set(tags),key=tags.count);cells=np.column_stack(np.nonzero(p.cc==tag));tree=cKDTree(cells[:,::-1]*p.step);anchors=[tree.data[tree.query(q)[1]] for q in anchors]
 for a,b in zip(anchors,anchors[1:]):
  q=p.path(a,b)
  if q is None:raise ValueError('Disconnected '+name)
  arr.extend(q if not arr else q[1:])
 raw=LineString(arr);line=LineString(xy(delta(raw.coords)));assert p.land.buffer(.0001).covers(line),name
 mandatory=sorted(set([0.,line.length]+[line.project(Point(a)) for a in anchors]));chosen=[]
 for t in mandatory:
  if all(abs(t-v)>.55 for v in chosen):chosen.append(t)
 for t in np.arange(0,line.length,1.0 if mode=='metro' else .9):
  if all(abs(t-v)>.55 for v in chosen):chosen.append(float(t))
 ds=sorted(chosen);st=[];nd=[]
 for i,t in enumerate(ds):
  q=np.array(line.interpolate(float(t)).coords[0]);pos=Point(q)
  if any(pos.distance(Point(np.array(s['c'])/20))<.45 for s in st):continue
  if p.rivers.distance(pos)<.05:continue
  label=names[min(len(names)-1,int(t/max(.01,line.length)*(len(names))))]+('' if i in [0,len(ds)-1] else ['南坊','西里','东坊','北里','学舍','市集','驿前'][i%7]);s={'n':label,'c':(q*20).round(3).tolist()};st.append(s)
  if mode=='metro':
   s.update(l=[len(c['ml'])],s=((q-c['w']/2)*2).round(3).tolist());near=next((j for j,n in enumerate(c['mn']) if np.linalg.norm(np.array(n['c'])/20-q)<.002),None)
   if near is None:nd.append(len(c['mn']));c['mn'].append(s)
   else:nd.append(near);c['mn'][near]['l'].append(len(c['ml']));st[-1]=c['mn'][near]
 l=dict(n=name,col=col,k='line' if mode=='metro' else 'lrt',s='规划',ring=0,km=round(line.length,3),q=delta(line.coords),op=0,xr=[],alignment_v24='实际DEM、连续道路、城址与山麓平原约束；未作工程可行性论证')
 if mode=='metro':l['nd']=nd;c['ml'].append(l)
 else:l['st']=st;c['lrt'].append(l)
 offsets=[line.distance(Point(np.array(s['c'])/20))*1000 for s in st];samples=np.array([line.interpolate(float(t)).coords[0] for t in np.linspace(0,line.length,max(3,round(line.length/.1)))]);heights=ndimage.map_coordinates(p.dem24,[samples[:,1]/p.cell24,samples[:,0]/p.cell24],order=1,mode='nearest');report=dict(name=name,mode=mode,km=l['km'],stations=len(st),vertices=len(arr),max_elevation_m=round(float(heights.max()),1),max_station_offset_m=max(offsets,default=0),land_only=p.land.buffer(.0001).covers(line),geometry_sha256=hashlib.sha256(dumps(l['q']).encode()).hexdigest());validation.append({'city':c['k'],**report});return report

def build():
 start=time.time()
 with ThreadPoolExecutor(max_workers=3) as pool:
  fh=pool.submit(osm,'hainan');ft=pool.submit(osm,'taiwan');dems={}
  for k,c in cities.items():dems[k]=terrain(c);print('DEM',k,dems[k][0].shape,round(time.time()-start),flush=True)
  references={'hainan':fh.result(),'taiwan':ft.result()}
 for k,c in cities.items():
  dem,step=dems[k];ref=references['hainan' if k in ['qv20_zhuyai','qv20_daner','qv20_qiongdong','qv20_lingshui'] else 'taiwan'];prep_reference(c,dem,step,ref);p=TerrainPlan24(c,dem,step)
  if k!='q0065':c['ml']=[];c['mn']=[];c['lrt']=[];c['alt']={};c['ops']=[];c['xf']=[]
  lines=[add_line(c,TerrainPlan24(c,dem,step),*spec) for spec in SPECS[k]]
  c['metro'].update(nl=len(c['ml']),nst=len(c['mn']),km=round(sum(l['km'] for l in c['ml'] if l['s']=='运营'),3),kmp=round(sum(l['km'] for l in c['ml'] if l['s']!='运营'),3),total_km=round(sum(l['km'] for l in c['ml']),3),lrtkm=round(sum(l['km'] for l in c['lrt']),3),ring=0,ninter=sum(len(n['l'])>1 for n in c['mn']))
  c['transit_v24']=dict(policy='以既有铁路、轻轨与公交接驳服务实际聚落，地铁限于连续建成区骨干',note='各线为架空近期规划；走廊按现代地形、海陆、水系与道路参照筛选，尚需客流及工程研究',feeders=['外围村落采用公交与铁路接驳，保护山地与河口湿地。','规划线路不作为已运营交通，站距随聚落与河流条件调整。'],new_lines=lines)
  s=cityBy[k];s.update(nl=len(c['ml']),km=c['metro']['total_km'],ml=[dict(n=l['n'],col=l['col'],s=l['s'],q=delta(world(c,xy(l['q'])),10000)) for l in c['ml']],ms=[dict(n=n['n'],c=world(c,np.array(n['c'])/20).round(7).tolist(),i=len(n['l'])>1,w=4 if len(n['l'])>1 else 1) for n in c['mn']],lr=[dict(n=l['n'],col=l['col'],s='规划',q=delta(world(c,xy(l['q'])),10000)) for l in c['lrt']],lst=[dict(n=s['n'],c=world(c,np.array(s['c'])/20).round(7).tolist()) for l in c['lrt'] for s in l['st']]);A['c/'+k+'.json']=encode(c);reports.append(dict(city=k,name=c['n'],metro=c['metro'],lines=lines,reference_roads=len(c['road']),reference_rivers=len(c['riv'])));print('Planned',k,[(l['name'],l['km']) for l in lines],flush=True)
 old=oldD();D['p500']=copy.deepcopy(old['p500']);D['wei17']=copy.deepcopy(old['wei17']);D['L']['weiline']=copy.deepcopy(old['L']['weiline']);D.get('v23',{}).pop('frontier',None)
 k='wdf268c';c=decode(A['c/'+k+'.json']);c['st']='北魏';c['nom']='东北界恢复为保留的 v22 轮廓';A['c/'+k+'.json']=encode(c);cityBy[k]['st']='北魏';cityBy[k].pop('pol',None)
 D['c20']['nm']=sum(s.get('nl',0)>0 for s in C['city']);D['c20']['nst']=sum(len(s.get('ms',[])) for s in C['city']);D['v24']={'wei_restoration':{'source_commit':'c377eebcdac17b11c36ef2cf1fd094d92e8dee70','source_version':'v22','exact_p500':True,'exact_wei17':True,'exact_weiline':True},'planning':'独立海岛与晋安近期规划'};A['l_city.json']=encode(C)
 for name,(prefix,data) in FILES.items():
  for key in data:
   if key in A:data[key]=A[key]
  (O/'data'/name.replace('v23','v24')).write_text(prefix+'='+dumps(data)+';')
 (O/'data/v24_d.js').write_text('document.getElementById("data").textContent='+json.dumps(encode(D))+';');(O/'planning-v24.json').write_text(json.dumps(dict(revision='v24-r1',cities=reports,sources=['https://registry.opendata.aws/terrain-tiles/','https://www.openstreetmap.org/copyright','https://data.gov.tw/dataset/73232'],caveat='现代地貌参照下的架空规划，不作为施工方案'),ensure_ascii=False,indent=2));(O/'validation-v24.json').write_text(json.dumps(dict(revision='v24-r1',wei_restoration=D['v24']['wei_restoration'],lines=validation),ensure_ascii=False,indent=2));pickle.dump((D,A,FILES,C,cities),open(T/'result.pkl','wb'));print('v24 data complete',round(time.time()-start),'seconds',flush=True)
if __name__=='__main__':build()
