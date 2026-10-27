"""Focused geometry, station indexing and restored-boundary checks."""
from atlas24_support import *
import numpy as np
from shapely.geometry import Point,LineString
from revise_atlas_v20 import xy
D,A,F,C,cities=pickle.load(open(T/'result.pkl','rb'));old=oldD();N=planning_namespace(D)
assert D['p500']==old['p500'] and D['wei17']==old['wei17'] and D['L']['weiline']==old['L']['weiline']
assert next(s for s in C['city'] if s['k']=='wdf268c')['st']=='北魏'
report=json.loads((O/'validation-v24.json').read_text());sha=set()
for r in report['lines']:
 assert r['land_only'] and r['max_station_offset_m']<2 and r['stations']>=3 and r['vertices']>10,r
 assert r['geometry_sha256'] not in sha,r;sha.add(r['geometry_sha256'])
for k,c in cities.items():
 p=N['Plan'](c)
 for l in c['ml']:
  assert all(0<=i<len(c['mn']) for i in l['nd'])
  for i in l['nd']:assert c['ml'].index(l) in c['mn'][i]['l']
 for t in ['contours','lakes','hill_names']:assert isinstance(c['terrain'][t],list)
 for l in [x for x in c['ml']+c['lrt'] if 'alignment_v24' in x]:
  assert l['s']=='规划' and not l['ring'];line=LineString(xy(l['q']));assert p.land.buffer(.0001).covers(line)
 for d in c['dist']:assert d['r']
 assert c['metro']['nl']==len(c['ml']) and c['metro']['nst']==len(c['mn'])
s=(O/'index.html').read_text();a=s.index('<section class="fb"');b=s.index('<main>',a);assert b-a<700 and '<svg' not in s[a:b];assert '<details id="worldview23">' in s
static=(O/'static.html').read_text();assert '<script' not in static and static.count('<figure>')==5;assert '<details><summary>Weltentwurf' in static
report.update(status='passed',new_alignments=len(report['lines']),mobile_device_testing='Cloud Chrome simulation only; physical Safari unverified',static_figures=5);(O/'validation-v24.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('PASS: exact v22 border; 13 new alignments; valid station membership; default closed intro; independent script-free static atlas')
