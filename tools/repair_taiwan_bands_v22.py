"""Remove disconnected scan-row fragments from the terrain catchment partition.

Keep seven activity areas and the exact detailed island coastline. Shared borders
are simplified as one coverage, not as separate overlapping polygons.
"""
from pathlib import Path
import json,numpy as np,shapely
from shapely.geometry import Polygon,box,shape
from shapely.ops import unary_union
from scipy import ndimage
from revise_atlas_v20 import decode,encode,xy,pack,polygons
R=Path(__file__).resolve().parents[1];p=R/'dist/data/v22_d.js';D=decode(json.loads(p.read_text().split('=',1)[1].strip().rstrip(';')))
index=next(i for i,a in enumerate(D['v20_ext']['islands']) if '台湾' in a['n']);island=json.loads((R/'tools/taiwan-partition-base-v21.json').read_text());D['v20_ext']['islands'][index]=island
coasts=json.loads((R/'tools/island-coasts-v21.geojson').read_text());coast=next(shape(f['geometry']) for f in coasts['features'] if f['properties']['name']=='台湾')
step=.003;minx,miny,maxx,maxy=coast.bounds;x=np.arange(minx-step,maxx+step,step);y=np.arange(miny-step,maxy+step,step);xx,yy=np.meshgrid(x,y);land=shapely.contains_xy(coast,xx,yy);labels=np.full(xx.shape,-1,dtype=np.int16);kept=[];before=[]
for i,a in enumerate(island['areas']):
 g=shapely.symmetric_difference_all([Polygon(xy(q,10000)).buffer(0) for q in a['r']]);m=shapely.contains_xy(g,xx,yy)&land
 components,n=ndimage.label(m,np.ones((3,3)));sizes=np.bincount(components.ravel());sizes[0]=0;main=components==int(np.argmax(sizes));before.append(int(n))
 core=ndimage.binary_erosion(main,iterations=2)
 if not core.any():core=main
 labels[core]=i;kept.append(core)
_,inds=ndimage.distance_transform_edt(labels<0,return_indices=True);labels=labels[tuple(inds)]
# A sub-kilometre shared generalization removes pixel stair steps at the margins.
scores=np.stack([ndimage.gaussian_filter((labels==i).astype(float),1.6) for i in range(len(kept))]);labels=np.argmax(scores,axis=0)
parts=[]
for i in range(len(kept)):
 spans=[]
 for row in range(len(y)):
  cells=np.flatnonzero((labels[row]==i)&land[row])
  for run in np.split(cells,np.flatnonzero(np.diff(cells)>1)+1):
   if len(run):spans.append(box(x[run[0]]-step/2,y[row]-step/2,x[run[-1]]+step/2,y[row]+step/2))
 parts.append(unary_union(spans).intersection(coast))
missing=coast.difference(unary_union(parts))
for g in polygons(missing):
 i=min(range(len(parts)),key=lambda i:parts[i].distance(g.representative_point()));parts[i]=unary_union([parts[i],g])
parts=list(shapely.coverage_simplify(parts,.005,simplify_boundary=False))
gap=coast.symmetric_difference(unary_union(parts)).area;overlap=sum(g.area for g in parts)-unary_union(parts).area
assert gap<1e-8 and overlap<1e-8,(gap,overlap)
for a,g in zip(island['areas'],parts):
 a['r']=pack(g);pt=g.representative_point();a['c']=[pt.x,pt.y]
island['note']=island['note'].split(' v22：')[0]+' v22：清除成本分区中的孤立横向扫描条带，以连续主活动区重建共享边界；海岸保持原样。'
report={'revision':'v22','island':'台湾','activity_areas':len(parts),'scan_fragments_before':before,'coverage_gap_deg2':gap,'overlap_deg2':overlap,'coastline_unchanged':True,'method':'保留各区连续主区、清除孤立扫描行碎片，共享边界统一概化；不改海岸'}
(R/'dist/island-bands-v22.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));p.write_text('document.getElementById("data").textContent='+json.dumps(encode(D))+';')
print(report)
