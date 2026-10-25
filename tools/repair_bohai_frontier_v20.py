"""Repair the NE frontier seam and recompute only the Bohai maritime inset.

Keeps Northern Wei's restored outline byte-for-byte. Nomadic contact areas
are low-strength activity bands, separate from coastal maritime ownership.
"""
from pathlib import Path
import copy, hashlib, json, re
import numpy as np
from scipy.spatial import cKDTree
from pyproj import Transformer
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union, transform, voronoi_diagram
import shapely
from revise_atlas_v20 import decode, encode, xy, pack, dumps, polygons, GEOD

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT/'dist'
DATA = OUT/re.search(r'src="(data/v20[^\"]*_d\.js)"',(OUT/'index.html').read_text()).group(1)
REPORT = OUT/'bohai-frontier-v20.json'

def geom(rings, clip=None):
    """Read the atlas's even-odd rings, including interior voids."""
    result = Polygon()
    for r in rings:
        if len(r) < 8:
            continue
        q = xy(r, 10000)
        if clip is not None:
            b = clip.bounds
            if q[:,0].max()<b[0] or q[:,0].min()>b[2] or q[:,1].max()<b[1] or q[:,1].min()>b[3]:
                continue
        g = Polygon(q).buffer(0)
        if clip is not None:
            g = g.intersection(clip)
        result = result.symmetric_difference(g)
    return result.buffer(0)

def km2(g):
    return sum(abs(GEOD.geometry_area_perimeter(p)[0]) for p in polygons(g))/1e6

def xyz(ll):
    a = np.radians(ll)
    return np.c_[np.cos(a[:,1])*np.cos(a[:,0]), np.cos(a[:,1])*np.sin(a[:,0]), np.sin(a[:,1])]

def main():
    D = decode(json.loads(DATA.read_text().split('=',1)[1].rstrip(';')))
    previous = D.get('v20_ext',{}).get('bohai_frontier_repair',{})
    if previous.get('revision')=='v20-r3':
        print('Bohai/frontier repair is already applied; report:',REPORT)
        return
    polity = {s['en']:s for s in D['p500']}
    wei = polity['Toba Wei']
    original_outline = copy.deepcopy(wei['r'])
    extent = box(111,35,130,51)
    land = geom(D['world'],extent)
    W = geom(wei['r'],extent)
    released = geom(D['wei_frontier_legacy_v19']['r'],extent).difference(W)
    coastal_errors = {}
    adjacent = ['Kumoxi','Khitan']
    original_cores = {}
    for en in adjacent:
        s = polity[en]
        coastal_errors[en] = round(km2(geom(s['r'],extent).difference(land)),4)
        for key in ['r']:
            # v20 added all of the former outline's released pieces to every
            # strength tier, including detached coastal fragments.
            g = geom(s[key]).difference(released).difference(W)
            g = g.difference(extent.difference(land))
            s[key] = pack(g)
        original_cores[en] = geom(s['r'])
        for b in s['bands']:
            g = geom(b['r']).difference(released).difference(W)
            b['r'] = pack(g.difference(extent.difference(land)))
        s['maritime_v20'] = {'coastal':False,'reason':'本图核心居地为内陆松漠、河谷牧地；东北接触带不生成渤海海域。'}
        s['frontier_contact_v20'] = '恢复内陆核心；与北魏之间的窄缝接入低强度活动带，保持原北魏轮廓。'

    # Work within the screenshot's NE frontier. Only fill land components
    # touching Wei; wider unrecorded regions elsewhere remain unchanged.
    roi = box(113.0507,39.5,124.8,44.6)
    settled = [W.intersection(roi)]
    nomads = []
    for s in D['p500']:
        if s.get('nm') == 1:
            nomads.append(geom(s['bands'][0]['r'],roi))
        elif s['en'] != 'Toba Wei':
            settled.append(geom(s.get('fb') or s['r'],roi))
    covered = unary_union(settled+nomads)
    gaps = land.intersection(roi).difference(covered)
    selected = [g for g in polygons(gaps)
                if 0.002<km2(g)<30000 and
                (g.distance(W)<.0002 or
                 (not g.intersects(roi.boundary) and g.representative_point().y>41.8))]
    missing = unary_union(selected)
    forward = Transformer.from_crs('EPSG:4326','+proj=aeqd +lat_0=42 +lon_0=120 +datum=WGS84 +units=m',always_xy=True).transform
    inverse = Transformer.from_crs('+proj=aeqd +lat_0=42 +lon_0=120 +datum=WGS84 +units=m','EPSG:4326',always_xy=True).transform
    # Shared contact pieces follow the nearest retained core boundary, rather
    # than a straight split between polity label positions.
    seeds=[]; owner=[]
    for j,en in enumerate(adjacent):
        core=transform(forward,original_cores[en])
        for p in polygons(core):
            ring=LineString(p.exterior.coords)
            for t in np.arange(0,ring.length,10000):
                seeds.append(ring.interpolate(t));owner.append(j)
    cloud=shapely.MultiPoint(seeds)
    cells=voronoi_diagram(cloud,envelope=transform(forward,roi).envelope.buffer(100000))
    tree=cKDTree(np.array([[p.x,p.y]for p in seeds]))
    pieces={en:[] for en in adjacent}
    projected=transform(forward,missing)
    for cell in cells.geoms:
        hit=cell.intersection(projected)
        if hit.is_empty:
            continue
        j=tree.query(np.array(cell.representative_point().coords[0]))[1]
        pieces[adjacent[owner[j]]].append(transform(inverse,hit))
    added={}
    for en in adjacent:
        g=unary_union(pieces[en]).intersection(land).difference(W)
        added[en]=round(km2(g),4)
        for b in polity[en]['bands']:
            if b['t'] <= .15:
                # A small overlap with the existing band prevents decimal
                # coordinate quantization from re-opening hairline seams.
                add=transform(inverse,transform(forward,g).buffer(20)).intersection(land).difference(W)
                b['r']=pack(unary_union([geom(b['r']),add]))
    coverage_after=unary_union(settled+[geom(s['bands'][0]['r'],roi)for s in D['p500']if s.get('nm')==1])
    residual=missing.difference(coverage_after)

    # Rebuild the enclosed sea inset from actual coastal polities. Do not use
    # nomadic influence bands as coastal frontage or as maritime base points.
    sea_box=box(117.25,37,123.25,41.5)
    sea=sea_box.difference(land)
    old_eez=D['v20_ext']['eez']
    samples=[];ids=[];coastal=[]
    for s in D['p500']:
        if not s.get('c') or s.get('nm')==1 or s.get('maritime_v20',{}).get('coastal') is False:
            continue
        g=geom(s.get('fb')or s['r'],extent)
        if g.is_empty:
            continue
        shore=land.boundary.intersection(g.buffer(.025))
        lines=[shore]if shore.geom_type=='LineString'else [v for v in getattr(shore,'geoms',[])if v.geom_type=='LineString']
        lines=[l for l in lines if not l.is_empty and l.length>.00001]
        if not lines:
            continue
        idx=len(coastal);coastal.append(s)
        for l in lines:
            for t in np.linspace(0,l.length,max(2,int(l.length/.02)+1)):
                p=l.interpolate(t);samples.append([p.x,p.y]);ids.append(idx)
    coast_tree=cKDTree(xyz(np.array(samples)))
    step=.025
    xs=np.arange(117.25+step/2,123.25,step);ys=np.arange(37+step/2,41.5,step)
    xx,yy=np.meshgrid(xs,ys)
    chord,nearest=coast_tree.query(xyz(np.c_[xx.ravel(),yy.ravel()]))
    labels=np.array(ids)[nearest].reshape(xx.shape)
    assert (2*6371*np.arcsin(np.clip(chord/2,0,1))).max()<370.4
    local={}
    for idx,s in enumerate(coastal):
        rects=[]
        for row,y in enumerate(ys):
            cols=np.where(labels[row]==idx)[0]
            if not len(cols):continue
            groups=np.split(cols,np.where(np.diff(cols)>1)[0]+1)
            for a in groups:
                rects.append(box(xs[a[0]]-step/2,y-step/2,xs[a[-1]]+step/2,y+step/2))
        g=unary_union(rects).intersection(sea) if rects else Polygon()
        if km2(g)>.0001:local[s['zh']]=g
    zones=[]
    for z in old_eez['zones']:
        if z['n'] in [polity[en]['zh']for en in adjacent]:
            continue
        inset=geom(z['r'],sea_box)
        if inset.is_empty and z['n']not in local:
            zones.append(z);continue
        g=unary_union([geom(z['r']).difference(sea_box),local.get(z['n'],Polygon())])
        if g.is_empty:continue
        z['r']=pack(g)
        if z['n']=='北魏':
            p=local[z['n']].representative_point();z['c']=[p.x,p.y]
        zones.append(z)
    existing={z['n']for z in zones}
    for s in coastal:
        if s['zh']in local and s['zh']not in existing:
            g=local[s['zh']];p=g.representative_point()
            zones.append(dict(n=s['zh'],el=s.get('el',s['zh']),r=pack(g),c=[p.x,p.y]))
    old_eez['zones']=zones
    old_eez['coastal_rule']='仅以沿海政权的海岸接触段取样；契丹、库莫奚的内陆活动带不产生海域；渤海湾以 0.025° 网格和原海岸裁切细化。'
    inset_zones=[(z['n'],geom(z['r'],sea_box))for z in zones]
    inset_zones=[(n,g)for n,g in inset_zones if km2(g)>.0001]
    missing_sea=sea.difference(unary_union([g for _,g in inset_zones]))
    overlaps=sum(km2(a.intersection(b))for i,(_,a)in enumerate(inset_zones)for _,b in inset_zones[i+1:])
    assert wei['r']==original_outline, 'Restored Wei outline must not change'
    assert all(n not in ['契丹','库莫奚']for n,_ in inset_zones)
    assert km2(residual)<1, ('frontier residual',km2(residual))
    assert km2(missing_sea)<1, ('maritime residual',km2(missing_sea))
    assert overlaps<1, ('maritime overlap',overlaps)
    report={
        'revision':'v20-r3','wei_outline_unchanged':True,
        'wei_outline_sha256':hashlib.sha256(dumps(original_outline).encode()).hexdigest(),
        'removed_nomadic_water_fragments_km2':coastal_errors,
        'filled_frontier_components':len(selected),'contact_area_km2':added,
        'frontier_residual_gap_km2':round(km2(residual),6),
        'Bohai_owners':{n:round(km2(g),3)for n,g in inset_zones},
        'Bohai_unassigned_water_km2':round(km2(missing_sea),6),
        'Bohai_overlap_km2':round(overlaps,6),'eez_zones':len(zones),
        'interpretation':'北魏轮廓原样保留；补齐区属于相邻部族低强度活动带，海域按沿海政权的真实海岸接触段重新分配。'}
    D['v20_ext']['bohai_frontier_repair']=report
    DATA.write_text('document.getElementById("data").textContent='+json.dumps(encode(D))+';')
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
