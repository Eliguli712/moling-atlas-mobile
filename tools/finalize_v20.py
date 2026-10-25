from pathlib import Path
import base64,gzip,json,copy,re,hashlib
import numpy as np
from shapely.geometry import Point,LineString,Polygon,box
from shapely.ops import unary_union,voronoi_diagram
from revise_atlas_v20 import decode,encode,xy,delta,pack,unpack,dumps,polygons,area
R=Path(__file__).resolve().parent.parent;OUT=R/'dist';A={};files={}
for p in sorted((OUT/'data').glob('*a*.js')):
    o=json.loads(p.read_text().split('=',1)[1].rstrip(';'));files[p]=o;A.update(o)
def put(k,c):
    for o in files.values():
        if k in o:o[k]=encode(c);return
    raise KeyError(k)
D=decode(json.loads((OUT/'data/v20_d.js').read_text().split('=',1)[1].rstrip(';')))
C=decode(A['l_city.json']);cindex={c['k']:c for c in C['city']}
# Connect intercity access lines to the actual metro interchange node, sharing
# the physical station and coordinates rather than merely drawing nearby lines.
local_links={}
for k in ['q0014','q0015','q0016','q0040','q0002']:
    c=decode(A['c/'+k+'.json']);hub=min(c['mn'],key=lambda n:sum((np.array(n['c'])/20-c['w']/2)**2));changed=0
    for l in c['xp']:
        if not l.get('n','').endswith(('铁路','公路','通道')):continue
        pts=xy(l['q']);h=np.array(hub['c'])/20;i=int(np.argmin(np.linalg.norm(pts-h,axis=1)))
        pts=np.vstack([pts[:i+1],h,pts[i:]])
        l['q']=delta(pts);l['st']=[dict(n=c['n']+'干线西接轨',c=np.round(pts[0]*20,3).tolist()),dict(n=hub['n'],c=hub['c']),dict(n=c['n']+'干线东接轨',c=np.round(pts[-1]*20,3).tolist())]
        l['interchange_v20']=dict(name=hub['n'],metro_lines=hub['l'],same_node=True);changed+=1
    local_links[k]=dict(city=c['n'],links=changed,hub=hub['n']);put('c/'+k+'.json',c)

# The old nominal outline had masked nomadic fields beyond the restored NE
# border. Return that surrendered margin to the adjoining original polities.
W=next(s for s in D['p500'] if s['en']=='Toba Wei');old=unpack(D['wei_frontier_legacy_v19']['r']);now=unpack(W['r']);released=old.difference(now).intersection(box(113.05,38,132,50));ne=[s for s in D['p500'] if s['en'] in ['Khitan','Kumoxi']]
from shapely.geometry import MultiPoint
cells=voronoi_diagram(MultiPoint([(s['lon'],s['lat']) for s in ne]),envelope=released.envelope.buffer(5))
for s in ne:
    cell=next(c for c in cells.geoms if c.covers(Point(s['lon'],s['lat'])));g=released.intersection(cell)
    if not g.is_empty:
        s['r']=pack(unary_union([unpack(s['r']),g]).difference(now))
        for band in s.get('bands',[]):
            if isinstance(band,dict) and 'r' in band:band['r']=pack(unary_union([unpack(band['r']),g]).difference(now))
        s['border_restoration_v20']='东北恢复原界后，旧名义领土遮罩之外归回相邻诸部。'

# New planned-city counters are independent of operating kilometre totals.
new=[c for c in C['city'] if c['k'].startswith('qv20_')]
D['c20']['nst']=18200+sum(len(c['ms']) for c in new);D['c20']['new_planned_metro_lines']=sum(c['nl'] for c in new)
put('l_city.json',C)
for p,o in files.items():p.write_text(p.read_text().split('=',1)[0]+'='+dumps(o)+';')
(OUT/'data/v20_d.js').write_text('document.getElementById("data").textContent='+json.dumps(encode(D))+';')
(OUT/'connectivity-v20.json').write_text(json.dumps(local_links,ensure_ascii=False,indent=2))
(R.parent/'analysis/v20-world.json').write_text(dumps(D))
print('Connected',local_links)
