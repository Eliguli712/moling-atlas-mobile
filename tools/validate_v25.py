"""Compare Wei to v24 and check every city against retained local terrain."""
from atlas25_support import *
from atlas24_support import planning_namespace
import hashlib,shapely,numpy as np
from shapely.geometry import Point,LineString
base,_,_,_=baseline25();D,A,F,C=pickle.load(open(T/'result.pkl','rb'));N=planning_namespace(D);geo=N['geo'];Plan=N['Plan'];errors=[]
wei=lambda d:next(s for s in d['p500'] if s['en']=='Toba Wei')
assert wei(D)==wei(base),'Wei polity changed'
for key in ['wei17','wei_nominal_v15']:assert D[key]==base[key],key
assert D['L']['weiline']==base['L']['weiline']
f=D['v25']['frontier'];outer=geo(f['extent_r'],10000);core=geo(f['control_r'],10000);dispute=geo(f['dispute_r'],10000);weak=geo(f['influence_r'],10000);buf=geo(f['buffer_r'],10000)
for n,ll in [('龙城/和龙',[120.4508,41.5801]),('扶余',[124.85,43.45]),('辽东城',[123.1727,41.2578]),('安市',[122.85,40.7]),('建安',[122.45,40.4]),('卑沙',[121.95,39.15]),('旅顺',[121.25,38.8]),('国内城',[126.19,41.12])]:
 assert outer.buffer(.002).covers(Point(ll)),n+' outside extent'
 assert core.buffer(.002).covers(Point(ll)),n+' outside control'
assert f['dispute_owner']=='北魏' and 100<area(dispute)<4000
assert core.intersection(dispute).area<.00003
assert outer.symmetric_difference(core.union(weak).union(dispute)).area<.0003
assert len(f['contact_q']) and buf.area>0
assert next(s for s in C['city'] if s['k']=='wdf268c')['st']=='高句丽'
counts=dict(cities=0,roads=0,metro_lines=0,amenities=0,lake_crossing_km=0,offshore_road_km=0,local_alignments=0);seeds=set()
for summary in C['city']:
 c=decode(A['c/'+summary['k']+'.json']);p=Plan(c);counts['cities']+=1;seeds.add(c['planning_v23']['city_seed']);counts['amenities']+=len(c['amenities_v23'])
 for r in c['road']+c.get('expwy',[]):
  if len(r.get('q',[]))<4:continue
  bad=LineString(xy(r['q'])).intersection(p.water).length;counts['roads']+=1;counts['offshore_road_km']+=bad
  if bad>.01:errors.append([c['k'],'offshore road',r.get('n'),bad])
 for l in c['ml']:
  counts['metro_lines']+=1;assert all(0<=i<len(c['mn']) for i in l['nd'])
  for i in l['nd']:assert c['ml'].index(l) in c['mn'][i]['l']
  for q in l.get('v23_parts',[l['q']]):
   if len(q)<4:continue
   bad=LineString(xy(q)).intersection(p.lake).length;counts['lake_crossing_km']+=bad
   if bad>.01:errors.append([c['k'],'metro in lake',l['n'],bad])
 for l in c['ml']+c['lrt']:
  if not l.get('alignment_v24'):continue
  counts['local_alignments']+=1;assert l['s']=='规划' and not l['ring'];assert p.land.buffer(.0001).covers(LineString(xy(l['q'])))
 for a in c['amenities_v23']:
  if a['status']!='架空规划':continue
  land=p.land if a['kind'] in ['park','suburban_park','river_district'] else p.buildable
  if not land.buffer(.002).covers(Point(np.array(a['c'])/20)):errors.append([c['k'],'amenity in water',a['n']])
assert len(seeds)==262
for island in D['v20_ext']['islands']:
 land=geo(island['r'],10000);pieces=[geo(a['r'],10000) for a in island['areas']];union=shapely.union_all(pieces);assert land.symmetric_difference(union).area<2e-6;assert sum(a.area for a in pieces)-union.area<2e-6
landmarks=json.loads((O/'landmarks-research-v25.json').read_text())['landmarks'];assert len(landmarks)==11
for a in landmarks:assert a['sources'] and a['accuracy_note']
s=(O/'index.html').read_text();static=(O/'static.html').read_text();assert '<details id="worldview23">' in s;assert '<script' not in static and static.count('<figure>')==5
report=dict(revision='v25-r1',status='passed' if not errors else 'failed',wei_unchanged=True,wei_sha256=hashlib.sha256(dumps(wei(D)).encode()).hexdigest(),goguryeo=dict(actual_area_km2=area(core),weaker_influence_km2=area(weak),wei_dispute_km2=area(dispute),overlapping_claims_retained=True),checks=counts,historical_landmarks=len(landmarks),errors=errors,device_testing='See render-validation-v25.json; physical iPhone Safari unverified')
(O/'validation-v25.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False),flush=True);assert not errors
