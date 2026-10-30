"""Terrain-cost influence fields; every Goguryeo layer excludes frozen Wei land."""
from atlas26_support import *
import copy,gzip,hashlib,math
import numpy as np,shapely,contourpy
from shapely.geometry import Polygon,Point,box,LineString
from shapely.ops import unary_union,nearest_points
from scipy.interpolate import LinearNDInterpolator
from scipy.ndimage import distance_transform_edt,gaussian_filter,map_coordinates,zoom
from scipy.spatial import cKDTree
from skimage.graph import MCP_Geometric
D,A,F,C=baseline26();N=planning_namespace(D);geo=N['geo'];poly=N['poly'];parts=N['parts']
wei=next(s for s in D['p500'] if s['en']=='Toba Wei');gog=next(s for s in D['p500'] if s['en']=='Koguryo')
def sha(x):return hashlib.sha256(dumps(x).encode()).hexdigest()
frozen={k:sha(v) for k,v in dict(wei=wei,wei17=D['wei17'],weiline=D['L']['weiline'],wei_nominal=D['wei_nominal_v15']).items()}
wg=geo(wei['r'],10000);old=geo(gog['r'],10000);roi=box(118.3,37.2,134,46.4)
land=unary_union([poly(q,10000).intersection(roi) for q in D['world'] if len(q)>5 and poly(q,10000).intersects(roi)])
# A 2 km local grid reconstructs broad relief from retained official ETOPO2022
# contours. Modern relief is a planning reference, not a historical border claim.
sx=111.195*math.cos(math.radians(42));sy=111.195;step=2.;xs=np.arange(118.3,134+step/sx,step/sx);ys=np.arange(37.2,46.4+step/sy,step/sy);xx,yy=np.meshgrid(xs,ys);query=np.column_stack([xx.ravel()*sx,yy.ravel()*sy]);mask=shapely.contains_xy(land,xx,yy);w_mask=shapely.contains_xy(wg,xx,yy)
relief=json.loads(gzip.decompress((R/'tools/world-v14/l_world_relief_v14.json.gz').read_bytes()));points=[];elevations=[]
for height,rs in relief['land']:
 for q in rs:
  a=xy(q,10000);a=a[(a[:,0]>117.8)&(a[:,0]<134.5)&(a[:,1]>36.7)&(a[:,1]<46.9)]
  if len(a):points.extend(a);elevations.extend([height]*len(a))
for q in D['world']:
 a=xy(q,10000);a=a[(a[:,0]>117.8)&(a[:,0]<134.5)&(a[:,1]>36.7)&(a[:,1]<46.9)]
 if len(a):points.extend(a[::2]);elevations.extend([0]*len(a[::2]))
points=np.asarray(points);elevations=np.asarray(elevations);p=points*[sx,sy];interp=LinearNDInterpolator(p,elevations,fill_value=np.nan);dem=interp(query);missing=~np.isfinite(dem)
if missing.any():dem[missing]=elevations[cKDTree(p).query(query[missing])[1]]
dem=gaussian_filter(dem.reshape(xx.shape),.65);gy,gx=np.gradient(dem,step*1000);rough=abs(dem-gaussian_filter(dem,3));cost=1+9*np.hypot(gx,gy)+rough/260;cost=np.where(mask&~w_mask,cost,np.inf)
forts=[('扶余城',124.85,43.45),('辽东城',123.1727,41.2578),('新城',123.95,41.9),('国内城',126.19,41.12),('平壤',125.785,39.128),('卑沙城',121.95,39.15)]
available=np.column_stack(np.nonzero(mask&~w_mask));tree=cKDTree(np.column_stack([xs[available[:,1]]*sx,ys[available[:,0]]*sy]))
def seeds(ll):return [tuple(available[i]) for i in tree.query(np.asarray(ll)*[sx,sy])[1]]
gseeds=seeds([[lo,la] for n,lo,la in forts]);nseeds=seeds([[120.1,45.65],[122.7,46.0],[125.3,46.0],[128.1,46.0],[131.6,45.5]])
dg=MCP_Geometric(cost,sampling=(step,step)).find_costs(gseeds)[0];dn=MCP_Geometric(cost,sampling=(step,step)).find_costs(nseeds)[0]
prior=shapely.contains_xy(old,xx,yy);signed=(distance_transform_edt(prior)-distance_transform_edt(~prior))*step
legacy_d=decode(json.loads(generated_at('cc14b1ddbb303058cd706605494981432aa18ea3','dist/data/v24_d.js').decode().split('=',1)[1].strip().rstrip(';')))
legacy_g=next(s for s in legacy_d['p500'] if s['en']=='Koguryo');south_prior=shapely.contains_xy(geo(legacy_g['fb'],10000),xx,yy);south_signed=(distance_transform_edt(south_prior)-distance_transform_edt(~south_prior))*step
rng=np.random.default_rng(49726);noise=np.zeros_like(xx)
for wavelength,amp in [(128,10),(64,7),(32,4),(16,2.5),(8,1.4),(4,.65)]:
 n=(max(3,math.ceil(xx.shape[0]*step/wavelength)+2),max(3,math.ceil(xx.shape[1]*step/wavelength)+2));small=rng.normal(size=n);field=zoom(small,(xx.shape[0]/n[0],xx.shape[1]/n[1]),order=3)[:xx.shape[0],:xx.shape[1]];noise+=field*amp
noise*=np.clip(.65+rough/200,.65,1.1)
reach=np.zeros_like(dg);both=np.isfinite(dg)&np.isfinite(dn);reach[both]=dn[both]-dg[both];reach[np.isfinite(dg)&~np.isfinite(dn)]=1000
score=.64*signed+.36*reach+noise
blend=np.clip((yy-38.5)/.9,0,1);score=blend*score+(1-blend)*(south_signed+noise*.7)
# Water and Wei are impassable to the field solver. Keep an interior prior on
# Wei until exact vector subtraction, so the two visible borders meet exactly.
score[mask&~w_mask&~np.isfinite(dg)]=-10000
_,nearest_land=distance_transform_edt(~mask,return_indices=True);score[~mask]=score[tuple(nearest_land[:,~mask])]
cg=contourpy.contour_generator(x=xs,y=ys,z=score,fill_type='OuterOffset')
def filled_region(generator,level,high):
 pts,offsets=generator.filled(level,high);polys=[]
 for a,off in zip(pts,offsets):
  if len(off)<2:continue
  p=Polygon(a[off[0]:off[1]],[a[off[i]:off[i+1]] for i in range(1,len(off)-1)]).buffer(0)
  if not p.is_empty:polys.append(p)
 return unary_union(polys)
# A land-connected support excludes coastal registration slivers around the
# opposite side of Bohai Bay. No travel through water or frozen Wei is allowed.
reachable=mask&~w_mask&np.isfinite(dg);support_score=4-distance_transform_edt(~reachable)*step
support_cg=contourpy.contour_generator(x=xs,y=ys,z=support_score,fill_type='OuterOffset');support=filled_region(support_cg,0,5)
def region(level):return filled_region(cg,level,float(np.max(score)+1)).intersection(land).intersection(support).union(old.difference(roi)).difference(wg).buffer(0)
outer=region(-8);control=region(18).intersection(outer);middle=region(4).intersection(outer);inner=region(45).intersection(control);strong=region(85).intersection(inner)
urban=unary_union([Point(lo,la).buffer(.22) for n,lo,la in forts]).intersection(control)
def precise(g):
 # Preserve exact clipped intersections instead of rounding them off Wei edges.
 out=[]
 for p in shapely.get_parts(g):
  if p.geom_type!='Polygon':continue
  for ring in [p.exterior,*p.interiors]:
   a=np.round(np.asarray(ring.coords)*10000,6);out.append(np.diff(a,axis=0,prepend=[[0.,0.]]).round(6).ravel().tolist())
 return out
def store_region(g):
 # The tiny guard is below 0.2 mm and removes floating point overlay remnants.
 return precise(g.difference(wg.buffer(1e-9)))
extent_r=store_region(outer);outer=geo(extent_r,10000);control=control.intersection(outer);urban=urban.intersection(control);weak=outer.difference(control)
layers={.06:outer,.15:middle.intersection(outer),.3:control,.45:inner,.6:strong.union(urban).intersection(control),.75:urban}
for b in gog['bands']:b['r']=store_region(layers[b['t']]);b['f']=copy.deepcopy(b['r'])
gog.update(r=extent_r,fb=copy.deepcopy(extent_r),a=area(control),a2=area(outer),asph=area(control),a1=area(urban))
gog['fb_v14']=copy.deepcopy(extent_r)
if gog.get('ts'):gog['ts']=store_region(geo(gog['ts'],10000))
gog['cities']=[c for c in gog['cities'] if not wg.covers(Point(c['lon'],c['lat']))]
gog['intro']=gog['intro'].split(' v25 架空设定：')[0]+' v26：北魏固定疆界具有排他性；高句丽所有控制与影响强度层均排除北魏领土。外围采用既有ETOPO2022等高线插值的坡度通行代价与多尺度控制场，无经纬线切边。北魏境内城址保留北魏归属。'
policy=dict(version='v26',no_overlap_with_wei=True,basis='既有NOAA ETOPO2022等高线→2公里坡度/起伏通行代价→双方控制场竞争→多尺度扰动→北魏排他裁切；现代地形参照的架空范围',terrain_reference_points=len(points),terrain_grid_km=step,fractal_scales_km=[128,64,32,16,8,4],source=relief['meta'],no_surveyed_historical_border_claim=True)
gog['control_v25']=dict(actual_area_km2=area(control),influence_area_km2=area(weak),extent_area_km2=area(outer),note='北魏排他；所有强度层均不覆盖北魏。');gog['control_v26']=policy;gog['liaodong_v16']['rule']='v26 地形控制场；北魏固定疆界优先。北魏境内城址不划给高句丽。'
oldf=D['v25']['frontier'];dispute=geo(oldf['dispute_r'],10000).intersection(wg)
contact=wg.boundary.intersection(outer.buffer(.00001)).intersection(box(119,39.5,124,45)).difference(land.boundary.buffer(.02));assert contact.length>.1
buffer=contact.buffer(.075).intersection(outer).difference(wg);f={**oldf,'extent_r':extent_r,'control_r':store_region(control),'urban_r':store_region(urban),'influence_r':store_region(weak),'overlap_r':[],'dispute_r':precise(dispute),'contact_q':[delta(g.coords,10000) for g in parts(contact)],'buffer_r':store_region(buffer),'buffer_c':list(buffer.representative_point().coords[0]),'buffer_zh':'高句丽一侧接壤缓冲带','buffer_note':'仅位于高句丽一侧，不覆盖北魏固定领土。','dispute_basis':'沿用北魏境内广兴小区；高句丽控制/影响均排除此区。','reference':'用户 IMG_3054.jpeg：不得覆盖北魏，不使用直线边界。',**gog['control_v25']}
D['v25'].update(revision='v26-r1',frontier=f);D['v26']=dict(revision='v26-r1',wei_frozen=frozen,frontier_policy=policy)
restored=[]
for s in C['city']:
 if s.get('st')!='高句丽' or not wg.covers(Point(s['lon'],s['lat'])):continue
 c=decode(A['c/'+s['k']+'.json']);c['st']='北魏';c['nom']='固定北魏疆界内；高句丽控制与影响层均不进入。';A['c/'+s['k']+'.json']=encode(c);s['st']='北魏';s['pol']='Toba Wei';restored.append(dict(key=s['k'],name=s['n']))
A['l_city.json']=encode(C)
assert frozen=={k:sha(v) for k,v in dict(wei=wei,wei17=D['wei17'],weiline=D['L']['weiline'],wei_nominal=D['wei_nominal_v15']).items()}
for name,(prefix,data) in F.items():
 for key in data:
  if key in A:data[key]=A[key]
 (O/'data'/name.replace('v25','v26')).write_text(prefix+'='+dumps(data)+';')
(O/'data/v26_d.js').write_text('document.getElementById("data").textContent='+json.dumps(encode(D))+';');(O/'data/v26_rasters.js').write_bytes(generated_at(BASE,'dist/data/v25_rasters.js'))
np.savez_compressed(R/'tools/terrain-frontier-v26.npz',lon=xs,lat=ys,elevation_m=dem.astype('f4'),cost=cost.astype('f4'),score=score.astype('f4'))
report=dict(revision='v26-r1',wei_unchanged=True,wei_frozen=frozen,policy=policy,restored_wei_cities=restored,shared_contact_degrees=contact.length,actual_km2=area(control),outer_km2=area(outer),disputed_wei_km2=area(dispute))
(O/'planning-v26.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));pickle.dump((D,A,F,C),open(T/'result.pkl','wb'));print(json.dumps({k:v for k,v in report.items() if k not in ['policy','wei_frozen']},ensure_ascii=False),flush=True)
