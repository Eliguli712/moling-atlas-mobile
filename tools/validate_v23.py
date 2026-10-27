from pathlib import Path
import json,pickle,numpy as np,shapely
import revise_atlas_v23 as m
cs=pickle.load(open(m.T/'cities.pkl','rb'));errors=[];seeds=set();counts=dict(cities=len(cs),facilities=0,roads=0,metro_lines=0,offshore_road_km=0,lake_crossing_km=0)
for k,c in cs.items():
 p=m.Plan(c);seeds.add(c['planning_v23']['city_seed']);counts['facilities']+=len(c['amenities_v23']);assert len(c['amenities_v23'])>=9
 for r in c['road']+c.get('expwy',[]):
  if len(r.get('q',[]))<4:continue
  bad=m.LineString(m.xy(r['q'])).intersection(p.water).length;counts['roads']+=1;counts['offshore_road_km']+=bad
  if bad>.01:errors.append([k,'offshore road',r.get('n'),bad])
 for l in c['ml']:
  counts['metro_lines']+=1
  for q in l.get('v23_parts',[l['q']]):
   if len(q)<4:continue
   bad=m.LineString(m.xy(q)).intersection(p.lake).length;counts['lake_crossing_km']+=bad
   if bad>.01:errors.append([k,'metro in lake',l['n'],bad])
 for a in c['amenities_v23']:
  if a['status']!='架空规划':continue
  land=p.land if a['kind'] in ['park','suburban_park','river_district'] else p.buildable
  if not land.buffer(.002).covers(m.Point(np.array(a['c'])/20)):errors.append([k,'amenity in water',a['n']])
assert len(seeds)==len(cs),'duplicate city seed'
d=m.decode(json.loads((m.O/'data/v23_d.js').read_text().split('=',1)[1].strip().rstrip(';')));g=m.geo(next(s for s in d['p500'] if s['en']=='Koguryo')['r'],10000);w=m.geo(next(s for s in d['p500'] if s['en']=='Toba Wei')['r'],10000);shared=g.boundary.intersection(w.boundary);assert shared.length>2.5;assert g.intersection(w).area<1e-8
for n,ll in [('龙城',[120.4508,41.5801]),('扶余',[124.85,43.45]),('辽东城',[123.1727,41.2578]),('卑沙',[121.95,39.15]),('旅顺',[121.25,38.8])]:assert g.buffer(.001).covers(m.Point(ll)),n
buf=m.geo(d['v23']['frontier']['buffer_r'],10000);assert shared.difference(buf.buffer(.002)).length<.01
for i in d['v20_ext']['islands']:
 land=m.geo(i['r'],10000);pieces=[m.geo(a['r'],10000) for a in i['areas']];union=shapely.union_all(pieces);assert land.symmetric_difference(union).area<2e-6;assert sum(a.area for a in pieces)-union.area<2e-6
out=dict(revision='v23',checks=counts,unique_city_seeds=len(seeds),wei_koguryo_shared_border_degrees=shared.length,wei_koguryo_overlap_degrees2=g.intersection(w).area,errors=errors)
(m.O/'validation-v23.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(out,ensure_ascii=False)[:5000]);assert not errors
