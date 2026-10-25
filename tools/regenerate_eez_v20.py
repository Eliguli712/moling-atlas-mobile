from pathlib import Path
import json,math
import numpy as np
import shapely
from scipy.spatial import cKDTree
from revise_atlas_v20 import decode,encode,pack,unpack,polygons
from shapely.ops import unary_union
from shapely.geometry import Polygon
R=Path(__file__).resolve().parent.parent;OUT=R/'dist';PTH=OUT/'data/v20_d.js'
D=decode(json.loads(PTH.read_text().split('=',1)[1].rstrip(';')))
land=unpack(D['world']);shapely.prepare(land);islands=D['v20_ext']['islands']
# Offshore economic zones are separate from the 12-nautical-mile sea layer.
# Spherical nearest-coast allocation gives a bounded, reproducible schematic
# median line, rather than overlapping circular buffers around capital cities.
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
owners=[dict(n='南齐',el='Νότιον Τσί',r=pack(unary_union([unpack(D['L']['red'])]+[unpack(i['r']) for i in islands])))]
owners.extend(dict(n=s['zh'],el=s['el'],r=s['r']) for s in D['p500'] if s.get('c'))
coastband=land.boundary.buffer(.075);samples=[];sample_owners=[]
for i,o in enumerate(owners):
    country=unpack(o['r'])
    if country.is_empty:continue
    shore=country.boundary.intersection(coastband)
    for l in getattr(shore,'geoms',[shore]):
        if l.geom_type!='LineString' or l.length<.015:continue
        for t in np.linspace(0,l.length,max(2,int(l.length/.08)+1)):
            p=l.interpolate(t);samples.append([p.x,p.y]);sample_owners.append(i)
def xyz(ll):
    a=np.radians(ll);return np.c_[np.cos(a[:,1])*np.cos(a[:,0]),np.cos(a[:,1])*np.sin(a[:,0]),np.sin(a[:,1])]
lon=np.arange(-179.875,180,.25);lat=np.arange(-79.875,80,.25);xx,yy=np.meshgrid(lon,lat)
water=~shapely.contains_xy(land,xx,yy);ll=np.c_[xx[water],yy[water]]
distance,index=cKDTree(xyz(np.array(samples))).query(xyz(ll));km=2*6371*np.arcsin(np.clip(distance/2,0,1))
labels=np.full(xx.shape,-1,np.int16);owner=np.array(sample_owners)[index];owner[km>370.4]=-1;labels[water]=owner
zones=[]
for i,o in enumerate(owners):
    ys,xs=np.where(labels==i)
    if len(xs)<3:continue
    x0=max(0,xs.min()-2);x1=min(len(lon),xs.max()+3);y0=max(0,ys.min()-2);y1=min(len(lat),ys.max()+3)
    fig,ax=plt.subplots();cs=ax.contour(xx[y0:y1,x0:x1],yy[y0:y1,x0:x1],(labels[y0:y1,x0:x1]==i).astype(float),levels=[.5]);gs=[]
    for seg in cs.allsegs[0]:
        if len(seg)<4:continue
        g=Polygon(seg).buffer(0).simplify(.045)
        if not g.is_empty:gs.append(g)
    plt.close(fig)
    if gs:
        g=unary_union(gs).difference(land);p=g.representative_point();zones.append(dict(n=o['n'],el=o['el'],r=pack(g),c=[p.x,p.y]))
D['v20_ext']['eez']=dict(n='Αποκλειστική Οικονομική Ζώνη',abbr='ΑΟΖ',range_nm=200,range_km=370.4,zones=zones,
 note='架空海域规划：200海里范围；近岸采样与球面等距线概化，和12海里领海独立显示。')


PTH.write_text('document.getElementById("data").textContent='+json.dumps(encode(D))+';')
print('EEZ zones',len(zones))
