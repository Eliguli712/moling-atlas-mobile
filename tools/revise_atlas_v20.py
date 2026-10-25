"""Rebuild the uploaded v19 atlas with terrain-led rings and restored NE Wei.

Input is an unpacked, user-supplied distribution. No network is used.
The retained DEM is a planning reference, not a surveyed construction model.
"""
from pathlib import Path
import argparse, base64, copy, gzip, heapq, json, math, re
from collections import defaultdict
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
import shapely
from shapely.geometry import Polygon, LineString, Point, box, MultiPoint
from shapely.ops import unary_union, nearest_points, voronoi_diagram
from pyproj import Geod

ROOT=Path(__file__).resolve().parent.parent
GEOD=Geod(ellps='WGS84')
def dumps(x):return json.dumps(x,ensure_ascii=False,separators=(',',':'))
def decode(x):return json.loads(gzip.decompress(base64.b64decode(x)))
def encode(x):return base64.b64encode(gzip.compress(dumps(x).encode(),mtime=0)).decode()
def xy(q,scale=20):return np.cumsum(np.asarray(q,float).reshape(-1,2),axis=0)/scale
def delta(p,scale=20):
    a=np.round(np.asarray(p)*scale,3)
    return np.round(np.diff(a,axis=0,prepend=np.zeros((1,2))),3).ravel().tolist()
def polygons(g):return [g] if g.geom_type=='Polygon' else [p for p in getattr(g,'geoms',[]) if p.geom_type=='Polygon']
def unpack(rs):return unary_union([Polygon(xy(r,10000)).buffer(0) for r in rs])
def pack(g):
    # World ring encoding uses even/odd fill. Keep holes with their exterior.
    return [np.diff(np.rint(np.asarray(r.coords)*10000).astype(int),axis=0,prepend=[[0,0]]).ravel().tolist()
            for p in polygons(g) for r in [p.exterior,*p.interiors]]
def area(g):return round(sum(abs(GEOD.geometry_area_perimeter(p)[0]) for p in polygons(g))/1e6)

def restore_wei(D):
    s=next(s for s in D['p500'] if s['en']=='Toba Wei')
    original=unpack(D['wei_frontier_legacy_v12']['outline_r'])
    current=unpack(s['r']); control=unpack(s['wc'])
    # Stitch at an actual crossing of the old and new northern outlines.
    cross=original.boundary.intersection(current.boundary).intersection(box(112,40,119,44))
    points=list(cross.geoms) if hasattr(cross,'geoms') else [cross]
    seam=min(points,key=lambda p:abs(p.x-113.05)).x
    region=box(seam,38,132,50)
    restored=unary_union([current.difference(region),original.intersection(region)]).buffer(0)
    actual=unary_union([control.difference(region),original.intersection(region)]).intersection(restored)
    nominal=restored.difference(actual)
    D['wei_frontier_legacy_v19']={'r':s['r'],'wc':s['wc'],'wl':s['wl'],'wnom':copy.deepcopy(s['wnom'])}
    s.update(r=pack(restored),wc=pack(actual),wl=pack(nominal),a=area(restored))
    s['wnom'].update(aT=area(restored),aC=area(actual),aL=area(nominal),version='v20-NE-restored',
      note='东北段按内嵌 v12 原始轮廓恢复；营州—和龙与平州沿用原疆界。河西、河套西部保留原名义／实控分层。东北不再显示名义领土斜线。')
    D['wei_nominal_v15']['area_km2']={'nominal':s['wnom']['aT'],'control':s['wnom']['aC'],'nominal_only':s['wnom']['aL']}
    # Keep the retained county topology, clipping it to the restored envelope.
    W=D['wei17']; counties=W['xian']
    for x in counties:x['r']=pack(unpack(x['r']).intersection(restored));x['a']=area(unpack(x['r']))
    covered=unary_union([unpack(x['r']) for x in counties])
    # v17 omitted Yingzhou entirely. Restore its name from the retained city
    # catalogue and the pre-497 units in Wei shu 106 (exclude Zhengguang units).
    missing=original.intersection(region).difference(covered).buffer(0)
    ying=missing.intersection(box(119.15,39.7,124,44))
    seeds=[('龙城','昌黎郡',120.4508,41.5801),('广兴','昌黎郡',121.03,41.15),
           ('石城','建德郡',119.72,41.14),('广都','建德郡',119.7,41.82)]
    if not ying.is_empty:
        cells=voronoi_diagram(MultiPoint([(v[2],v[3]) for v in seeds]),envelope=ying.envelope.buffer(1))
        for n,j,lon,lat in seeds:
            cell=next(c for c in cells.geoms if c.covers(Point(lon,lat)))
            g=cell.intersection(ying)
            counties.append(dict(n=n,j=j,z='营州',lon=lon,lat=lat,a=area(g),p=0,r=pack(g),
              note='《魏书》卷106上：真君八年已有；辖境为原轮廓内的城址分区模型。'))
        W['zhou'].append(dict(n='营州',seat='和龙',lon=120.4508,lat=41.5801,r=pack(ying),a=area(ying),p=2451387,nj=2))
        for j in ['昌黎郡','建德郡']:
            cs=[x for x in counties if x['z']=='营州' and x['j']==j];g=unary_union([unpack(x['r']) for x in cs]);p=g.representative_point()
            W['jun'].append(dict(n=j,z='营州',zd=0,note='497 年框架；剔除正光以后所置郡县。',lon=p.x,lat=p.y,r=pack(g),a=area(g),p=0,nx=len(cs)))
    # Fill the small restored northern margins from their adjacent original
    # county, without changing the old internal arcs.
    missing=original.intersection(region).difference(unary_union([unpack(x['r']) for x in counties]))
    for g in polygons(missing):
        if g.area<1e-8:continue
        neighbours=[x for x in counties if x['r'] and x.get('z') in ['幽州','安州','平州','营州']]
        x=min(neighbours,key=lambda x:unpack(x['r']).distance(g.representative_point()))
        x['r']=pack(unary_union([unpack(x['r']),g]));x['a']=area(unpack(x['r']))
    for j in W['jun']:
        cs=[x for x in counties if x['z']==j['z'] and x['j']==j['n']]
        if cs:j['r']=pack(unary_union([unpack(x['r']) for x in cs]));j['a']=area(unpack(j['r']));j['nx']=len(cs)
    for z in W['zhou']:
        js=[j for j in W['jun'] if j['z']==z['n']]
        if js:z['r']=pack(unary_union([unpack(j['r']) for j in js]));z['a']=area(unpack(z['r']));z['nj']=len(js)
    W['note']+=' v20：东北外界恢复 v12；营州补回497年以前已有的昌黎、建德及龙城、广兴、石城、广都。'
    D['v20_border']={'source':'wei_frontier_legacy_v12.outline_r','stitch_lon':seam,'restored_region':[seam,38,132,50],
      'source_url':'https://zh.wikisource.org/zh-hans/魏書/卷106上#营州','NE_nominal_hatch_area_km2':area(nominal.intersection(region)),
      'original_NE_symmetric_difference_deg2':restored.intersection(region).symmetric_difference(original.intersection(region)).area}
    return D['v20_border']

class RingPlanner:
    def __init__(self,c):
        self.c=c
        p=ROOT/'tools/terrain-sample.npz' if c['k']=='q0000' else ROOT.parent/'analysis/terrain-cache'/f"{c['k']}.npz"
        if not p.exists():
            import zipfile
            with zipfile.ZipFile(ROOT/'tools/terrain-cache.zip') as z:
                import io
                if f"{c['k']}.npz" in z.namelist():
                    f=np.load(io.BytesIO(z.read(f"{c['k']}.npz")));self.dem=f['dem'].astype(float);self.step=float(f['step'])
                else:
                    from scipy.interpolate import griddata
                    self.step=.3;n=math.ceil(c['w']/self.step)+1;yy,xx=np.mgrid[:n,:n]
                    pts=[];heights=[]
                    for line in c.get('terrain',{}).get('contours',[]):
                        p=xy(line['q'])[::5];pts.extend(p);heights.extend([line['e']]*len(p))
                    if len(pts)>8:
                        self.dem=griddata(pts,heights,(xx*self.step,yy*self.step),method='linear')
                        near=griddata(pts,heights,(xx*self.step,yy*self.step),method='nearest');self.dem=np.where(np.isfinite(self.dem),self.dem,near)
                    else:self.dem=np.zeros((n,n))
        else:
            f=np.load(p);self.dem=f['dem'].astype(float);self.step=float(f['step'])
        self.h,self.w=self.dem.shape
        yy,xx=np.mgrid[:self.h,:self.w];self.xx=xx*self.step;self.yy=yy*self.step
        self.lakes=unary_union([Polygon(xy(p['r'])).buffer(0) for p in c['lake']+c['sea'] if not p.get('h')]+[Polygon(xy(p)).buffer(0) for p in c.get('terrain',{}).get('lakes',[])])
        self.water=unary_union([self.lakes]+[LineString(xy(r['q'])).buffer(max(.02,r['w']/2)) for r in c['riv']])
        self.wet=shapely.contains_xy(self.water,self.xx,self.yy);self.lk=shapely.contains_xy(self.lakes,self.xx,self.yy)
        gy,gx=np.gradient(self.dem,self.step*1000);self.slope=np.degrees(np.arctan(np.hypot(gx,gy)))
        rel=np.maximum(0,self.dem-ndimage.percentile_filter(self.dem,20,size=13))
        # Existing street corridors attract the route; high relief, lakes,
        # airport reserves and river-parallel running carry a higher cost.
        road=np.ones_like(self.wet)
        for r in c['road']:
            if r.get('k',3)>2:continue
            p=xy(r['q']);ix=np.clip(np.rint(p[:,0]/self.step).astype(int),0,self.w-1);iy=np.clip(np.rint(p[:,1]/self.step).astype(int),0,self.h-1);road[iy,ix]=False
        rd=ndimage.distance_transform_edt(road)*self.step
        self.cost=1+(self.slope/4)**2+np.minimum(9,rel/40)+np.minimum(2,rd)*.7+np.where(self.wet,24,0)
        hubs=[np.array(d['c'])/20 for d in c['dist']]
        hubs.extend(np.array(d['c'])/20 for d in c.get('historical_places',[]))
        if hubs:
            demand=cKDTree(hubs).query(np.c_[self.xx.ravel(),self.yy.ravel()])[0].reshape(self.dem.shape)
            self.stop_cost=self.cost+.55*np.minimum(demand,9)
        else:self.stop_cost=self.cost
        self.cost[self.lk]=180
        good=(~self.wet)&(self.slope<13)
        iy,ix=np.where(good);self.tree=cKDTree(np.c_[ix*self.step,iy*self.step]);self.good=good
        self.cache={}
    def cell(self,p):
        return (int(np.clip(round(p[1]/self.step),0,self.h-1)),int(np.clip(round(p[0]/self.step),0,self.w-1)))
    def leg(self,a,b):
        key=(tuple(a),tuple(b))
        if key in self.cache:return self.cache[key]
        if (key[1],key[0]) in self.cache:return self.cache[(key[1],key[0])][::-1]
        A=self.cell(a);B=self.cell(b);pad=max(5,math.ceil(2.8/self.step))
        lo=np.maximum(0,np.minimum(A,B)-pad);hi=np.minimum([self.h-1,self.w-1],np.maximum(A,B)+pad)
        def walk():
            q=[(0.,0.,A)];dist={A:0.};prev={};done=set()
            while q:
                _,d,u=heapq.heappop(q)
                if u in done:continue
                if u==B:
                    out=[B]
                    while out[-1]!=A:out.append(prev[out[-1]])
                    return np.array(out[::-1])[:,::-1]*self.step
                done.add(u)
                for dy,dx in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
                    v=(u[0]+dy,u[1]+dx)
                    if not(lo[0]<=v[0]<=hi[0] and lo[1]<=v[1]<=hi[1]):continue
                    dc=math.hypot(dx,dy)*(self.cost[u]+self.cost[v])*.5;nd=d+dc
                    if nd<dist.get(v,1e30):dist[v]=nd;prev[v]=u;heapq.heappush(q,(nd+math.hypot(v[0]-B[0],v[1]-B[1]),nd,v))
        p=walk()
        if p is None:p=np.array([a,b])
        p=np.vstack([a,p,b]);line=LineString(p).simplify(.065)
        # Round grid turns within the checked corridor; exact stations remain.
        p=np.array(line.coords)
        for _ in range(2):
            out=[p[0]]
            for u,v in zip(p,p[1:]):out.extend([u*.75+v*.25,u*.25+v*.75])
            out.append(p[-1]);p=np.array(out)
        smooth=LineString(p)
        if smooth.intersection(self.lakes).length<=line.intersection(self.lakes).length+.015:line=smooth
        self.cache[key]=np.array(line.coords);return self.cache[key]
    def revise(self):
        c=self.c;rings=[l for l in c['ml'] if l.get('ring') or l.get('k')=='halfring' or '全环' in l['n']]
        originals=copy.deepcopy(rings);moved={}
        occupied=np.array([n['c'] for n in c['mn']],float)/20
        for l in rings:
            for ni in l['nd']:
                n=c['mn'][ni]
                if len(n['l'])>2 or ni in moved:continue
                p=np.array(n['c'])/20;iy,ix=self.cell(p);rad=math.ceil(min(3.6,c['w']*.08)/self.step)
                y0=max(0,iy-rad);y1=min(self.h,iy+rad+1);x0=max(0,ix-rad);x1=min(self.w,ix+rad+1)
                dd=(self.xx[y0:y1,x0:x1]-p[0])**2+(self.yy[y0:y1,x0:x1]-p[1])**2
                sc=self.stop_cost[y0:y1,x0:x1]+dd*.16
                sc[~self.good[y0:y1,x0:x1]]=1e6
                near=np.flatnonzero((occupied[:,0]>x0*self.step-.2)&(occupied[:,0]<x1*self.step+.2)&(occupied[:,1]>y0*self.step-.2)&(occupied[:,1]<y1*self.step+.2))
                for other in near:
                    if other==ni:continue
                    sc[(self.xx[y0:y1,x0:x1]-occupied[other,0])**2+(self.yy[y0:y1,x0:x1]-occupied[other,1])**2<.18**2]=1e6
                if np.min(sc)>=1e6:continue
                j,k=np.unravel_index(np.argmin(sc),sc.shape);new=np.array([(k+x0)*self.step,(j+y0)*self.step])
                if np.linalg.norm(new-p)>.18:n['c']=np.round(new*20,3).tolist();moved[ni]=(p,new);occupied[ni]=new
        report=[]
        for l,old in zip(rings,originals):
            ps=[np.array(c['mn'][i]['c'])/20 for i in l['nd']]
            closed=bool(l.get('ring')) or '全环' in l['n']
            if closed and np.linalg.norm(ps[0]-ps[-1])>.01:ps.append(ps[0])
            parts=[]
            for a,b in zip(ps,ps[1:]):
                seg=self.leg(a,b);parts.extend(seg if not parts else seg[1:])
            line=LineString(parts);l['q']=delta(line.coords);l['km']=round(line.length,1)
            if '全环' in l['n']:l['ring']=1;l['k']='ring'
            l['terrain_aligned']=True;l['layout_v20']='terrain-street-corridor';l['xr']=[]
            for water,kind in [(self.water,'桥'),(self.lakes,'隧')]:
                for g in getattr(line.intersection(water),'geoms',[line.intersection(water)]):
                    if g.geom_type!='LineString' or g.length<.03:continue
                    p=g.interpolate(.5,normalized=True);l['xr'].append([round(p.x*20,3),round(p.y*20,3),kind])
            if not l['xr'] and np.max(self.slope)>15:l['grade_note']='山麓走廊，局部坡段保留隧道勘察。'
            errors=[line.distance(Point(p)) for p in ps]
            if max(errors,default=0)>.003:raise ValueError('Station disconnected '+c['k']+l['n'])
            report.append({'name':l['n'],'old_km':old['km'],'km':l['km'],'stops':len(l['nd']),
                'max_station_gap_km':round(max(errors,default=0),6),'crossings':len(l['xr']),
                'closed':closed,'closure_gap_km':round(np.linalg.norm(np.array(parts[0])-parts[-1]),6) if closed else None})
        # Light-rail stops sharing these physical stations follow the same node.
        for l in c['lrt']:
            changed=False
            for n in l['st']:
                if n.get('metro') in moved:n['c']=c['mn'][n['metro']]['c'];changed=True
            if changed:
                ps=[np.array(n['c'])/20 for n in l['st']];pts=[]
                for a,b in zip(ps,ps[1:]):pts.extend(self.leg(a,b))
                if pts:l['q']=delta(pts);l['km']=round(LineString(pts).length,1)
        # A two-line interchange can follow the town/valley corridor while
        # retaining its node identity. Reconnect every affected incident line.
        for l in c['ml']:
            if l in rings or not any(i in moved for i in l['nd']):continue
            ps=[np.array(c['mn'][i]['c'])/20 for i in l['nd']];pts=[]
            for a,b in zip(ps,ps[1:]):
                seg=self.leg(a,b);pts.extend(seg if not pts else seg[1:])
            if len(pts)>1:l['q']=delta(pts);l['km']=round(LineString(pts).length,1);l['interchange_reconnected_v20']=True
        c['ring_revision_v20']={'moved_local_stations':len(moved),'method':'300 m DEM, water and existing main streets; transfer nodes fixed','lines':report}
        return report

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    out=a.output;out.mkdir(exist_ok=True);(out/'data').mkdir(exist_ok=True)
    D=decode(json.loads((a.input/'data/v19_d.js').read_text().split('=',1)[1].rstrip(';')))
    files={};assets={}
    for p in sorted((a.input/'data').glob('*a*.js')):
        obj=json.loads(p.read_text().split('=',1)[1].rstrip(';'));files[p.name]=obj;assets.update(obj)
    report={'border':restore_wei(D),'cities':{}};changed={}
    for name,value in assets.items():
        if not name.startswith('c/'):continue
        c=decode(value)
        if not any(l.get('ring') or l.get('k')=='halfring' or '全环' in l['n'] for l in c['ml']):continue
        print('Planning',c['k'],c['n'],flush=True)
        p=RingPlanner(c);report['cities'][c['k']]=p.revise();changed[name]=c
    # City-level and world-level transit use the same revised geometry.
    summary=decode(assets['l_city.json'])
    P=D['proj']
    def ll(c,pts):
        a=np.asarray(pts);x=(c['o'][0]+a[...,0])*1000;y=(c['o'][1]-a[...,1])*1000;e=math.sqrt(P['E2']);rho=np.hypot(x,P['RHO0']-y);th=np.arctan2(x,P['RHO0']-y);q=P['QP']*(P['C']-(rho*P['N']/P['RA'])**2)/(2*P['N']);lat=np.arcsin(np.clip(q/P['QP'],-1,1))
        for _ in range(8):
            ss=np.sin(lat);v=(1-P['E2'])*(ss/(1-P['E2']*ss*ss)-np.log((1-e*ss)/(1+e*ss))/(2*e));lat+=(q-v)/(2*(1-P['E2'])*np.cos(lat)/(1-P['E2']*ss*ss)**2)
        return np.stack([(th/P['N']+P['L0'])*180/np.pi,lat*180/np.pi],axis=-1)
    for s in summary['city']:
        c=changed.get('c/'+s['k']+'.json')
        if not c:continue
        s['ml']=[dict(n=l['n'],col=l['col'],s={'运营':'运','在建':'建','规划':'规'}.get(l['s'],l['s']),k=l['k'],ring=l.get('ring',0),op=l.get('op',0),q=delta(ll(c,xy(l['q'])),10000),nd=l['nd']) for l in c['ml']]
        for n,raw in zip(s['ms'],c['mn']):n['c']=np.round(ll(c,np.array(raw['c'])/20),6).tolist()
        s['km']=round(sum(l['km'] for l in c['ml'] if l['s']=='运营'),1)
        if 'metro' in c:
            for k in ['km','okm']:
                if k in c['metro']:c['metro'][k]=s['km']
    changed['l_city.json']=summary
    for name,c in changed.items():
        for obj in files.values():
            if name in obj:obj[name]=encode(c);break
    for name,obj in files.items():
        target=name.replace('v19','v20');var='__NQ'+('A4_' if '_a4_' in name else 'A5_')+name.rsplit('_',1)[1].split('.')[0]
        (out/'data'/target).write_text('globalThis.'+var+'='+dumps(obj)+';')
    (out/'data/v20_d.js').write_text('document.getElementById("data").textContent='+json.dumps(encode(D))+';')
    html=(a.input/'index.html').read_text().replace('data/v19_','data/v20_')
    (out/'index.html').write_text(html)
    (out/'revision-v20.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    (ROOT.parent/'analysis/v20-world.json').write_text(dumps(D))
    for name,c in changed.items():
        p=ROOT.parent/'analysis/v20'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(dumps(c))
    print('Revised',len(report['cities']),'cities',sum(len(v) for v in report['cities'].values()),'rings',flush=True)

if __name__=='__main__':main()
