"""Release gates for the terrain frontier; frozen Wei is authoritative."""
from atlas26_support import *
import hashlib, math, re, subprocess
import numpy as np
from shapely.geometry import Point, box, LineString
import shapely

D,A,F,C=pickle.load((T/'result.pkl').open('rb'))
B,BA,BF,BC=baseline26();N=planning_namespace(D);geo=N['geo']
wei=next(s for s in D['p500'] if s['en']=='Toba Wei')
gog=next(s for s in D['p500'] if s['en']=='Koguryo')
bwei=next(s for s in B['p500'] if s['en']=='Toba Wei')
f=D['v25']['frontier'];wg=geo(wei['r'],10000)
def digest(x):return hashlib.sha256(dumps(x).encode()).hexdigest()
frozen=dict(wei=wei,wei17=D['wei17'],weiline=D['L']['weiline'],wei_nominal=D['wei_nominal_v15'])
assert wei==bwei
assert all(D[k]==B[k] for k in ['wei17','wei_nominal_v15'])
assert D['L']['weiline']==B['L']['weiline']
assert {k:digest(v) for k,v in frozen.items()}==D['v26']['wei_frozen']
assert {k:v for k,v in D.items() if k not in ['p500','v25','v26']}=={k:v for k,v in B.items() if k not in ['p500','v25','v26']}
assert [s for s in D['p500'] if s['en']!='Koguryo']==[s for s in B['p500'] if s['en']!='Koguryo']
checks={}
regions={k:gog[k] for k in ['r','fb','fb_v14','ts'] if gog.get(k)}
for i,b in enumerate(gog['bands']):
 for k in ['r','f']:regions[f'band_{i}_{k}']=b[k]
for k in ['extent_r','control_r','urban_r','influence_r','buffer_r']:regions[k]=f[k]
for k,r in regions.items():
 g=geo(r,10000);overlap=g.intersection(wg).area
 assert g.is_valid,(k,shapely.is_valid_reason(g))
 assert overlap==0,(k,overlap)
 checks[k]=dict(valid=True,wei_overlap_degrees2=overlap)
extent=geo(f['extent_r'],10000);control=geo(f['control_r'],10000)
assert len(list(shapely.get_parts(extent)))==1
assert extent.intersection(box(118,36,122.7,38.1)).area==0
assert geo(f['dispute_r'],10000).difference(wg).area<1e-9
assert not f['overlap_r']
assert control.difference(extent).area<1e-8
assert geo(f['urban_r'],10000).difference(control).area<1e-8
for i,b in enumerate(gog['bands'][1:],1):
 assert geo(b['r'],10000).difference(geo(gog['bands'][i-1]['r'],10000)).area<1e-8
anchors={}
for name,lo,la in [('扶余城',124.85,43.45),('辽东城',123.1727,41.2578),('安市城',122.95,41.1),('建安城',122.5,40.65),('卑沙城',121.95,39.15)]:
 p=Point(lo,la);assert extent.covers(p) and not wg.covers(p),name
 anchors[name]='高句丽'
helong=next(s for s in C['city'] if s['k']=='wdf268c');p=Point(helong['lon'],helong['lat'])
assert helong['st']=='北魏' and wg.covers(p) and not extent.covers(p)
anchors['和龙']='北魏'
assert all(not wg.covers(Point(s['lon'],s['lat'])) for s in C['city'] if s.get('st')=='高句丽')
assert all(not wg.covers(Point(s['lon'],s['lat'])) for s in gog['cities'])
changed=sorted(k for k in A if A[k]!=BA.get(k));assert changed==['c/wdf268c.json','l_city.json'],changed
# Inspect the free northern edge, excluding frozen shared boundary and coast.
sx=111.195*math.cos(math.radians(42));sy=111.195
coords=np.asarray(extent.exterior.coords);segments=[];runs=[];run=[]
for a,b in zip(coords[:-1],coords[1:]):
 mid=Point(*(a+b)/2)
 if min(a[1],b[1])>43.8 and mid.distance(wg)>.03:
  segments.append(float(np.linalg.norm((b-a)*[sx,sy])))
  if not run:run=[a]
  run.append(b)
 elif run:
  runs.append(np.array(run));run=[]
if run:runs.append(np.array(run))
assert len(segments)>200
assert max(segments)<5,max(segments)
deviations=[];ratios=[]
for run in runs:
 line=LineString(run*[sx,sy])
 for start in np.arange(0,line.length-25,12.5):
  sample=np.array([line.interpolate(t).coords[0] for t in np.linspace(start,start+25,31)])
  chord=LineString([sample[0],sample[-1]])
  deviations.append(max(Point(p).distance(chord) for p in sample))
  ratios.append(25/chord.length)
assert len(deviations)>15
assert float(np.median(deviations))>.3
assert float(np.median(ratios))>1.005
assert extent.bounds[1]>37.3 # no inherited 37.2-degree rectangular cut
s=(O/'index.html').read_text();assert "dataset.atlasRelease='v26-r1'" in s
assert 'selectedGog26(s26.g' in s and "ctx.clip(p,'evenodd')" in s
inline='\n'.join(re.findall(r'<script(?:\s[^>]*)?>([\s\S]*?)</script>',s))
(T/'syntax.js').write_text(inline);subprocess.run(['node','--check',str(T/'syntax.js')],check=True)
static=(O/'static.html').read_text();assert len(list(O.glob('static-*-v26.svg')))==5
assert '所有强度均排除北魏领土' in static
assert len(re.findall(r'<tr><td>',static))==262
report=dict(revision='v26-r1',status='passed',frozen_wei={k:digest(v) for k,v in frozen.items()},unchanged_other_polities=True,unchanged_transport_and_amenities=True,only_changed_city_archives=changed,exclusive_regions=checks,mainland_polygon_count=1,opposite_bohai_slivers=False,anchors=anchors,dispute_inside_wei=True,northern_free_frontier=dict(segments=len(segments),max_segment_km=max(segments),sample_windows=len(deviations),median_25km_chord_deviation_km=float(np.median(deviations)),median_arc_chord_ratio=float(np.median(ratios))),syntax='passed',static_figures=5,static_city_rows=262,terrain_source=D['v26']['frontier_policy']['source'])
(O/'validation-v26.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in report.items() if k not in ['exclusive_regions','terrain_source','frozen_wei']},ensure_ascii=False),flush=True)
