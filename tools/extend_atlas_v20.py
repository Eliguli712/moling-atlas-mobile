"""Add the requested island planning, Jiaozhou corridors and Greek labels."""
from pathlib import Path
import base64,copy,gzip,json,math,re
import numpy as np
from scipy.spatial import cKDTree
import shapely
from shapely.geometry import Polygon,Point,LineString,MultiPoint,box
from shapely.ops import unary_union,voronoi_diagram,transform
from pyproj import Geod
from revise_atlas_v20 import encode,decode,dumps,xy,delta,pack,unpack,polygons

R=Path(__file__).resolve().parent.parent;OUT=R/'dist';PTH=OUT/'data/v20_d.js'
D=decode(json.loads(PTH.read_text().split('=',1)[1].rstrip(';')));P=D['proj'];G=Geod(ellps='WGS84')
A={};files={}
for p in sorted((OUT/'data').glob('*a*.js')):
    obj=json.loads(p.read_text().split('=',1)[1].rstrip(';'));A.update(obj);files[p]=obj
def put(k,v):
    for obj in files.values():
        if k in obj:obj[k]=encode(v);return
    EXTRA[k]=encode(v)
EXTRA={};C=decode(A['l_city.json']);cities=C['city']
def forward(lon,lat):
    ss=np.sin(np.asarray(lat)*np.pi/180);e=math.sqrt(P['E2']);q=(1-P['E2'])*(ss/(1-P['E2']*ss*ss)-np.log((1-e*ss)/(1+e*ss))/(2*e));b=np.arcsin(q/P['QP']);th=P['N']*(np.asarray(lon)*np.pi/180-P['L0']);rho=P['RA']*np.sqrt(P['C']-2*P['N']*np.sin(b))/P['N'];return np.stack([rho*np.sin(th)/1000,(P['RHO0']-rho*np.cos(th))/1000],axis=-1)
def inverse(x,y):
    x=np.asarray(x)*1000;y=np.asarray(y)*1000;e=math.sqrt(P['E2']);rho=np.hypot(x,P['RHO0']-y);th=np.arctan2(x,P['RHO0']-y);q=P['QP']*(P['C']-(rho*P['N']/P['RA'])**2)/(2*P['N']);lat=np.arcsin(np.clip(q/P['QP'],-1,1))
    for _ in range(8):
        ss=np.sin(lat);v=(1-P['E2'])*(ss/(1-P['E2']*ss*ss)-np.log((1-e*ss)/(1+e*ss))/(2*e));lat+=(q-v)/(2*(1-P['E2'])*np.cos(lat)/(1-P['E2']*ss*ss)**2)
    return np.stack([(th/P['N']+P['L0'])*180/np.pi,lat*180/np.pi],axis=-1)
def local(c,p):
    a=forward(p[...,0],p[...,1]);return np.stack([a[...,0]-c['o'][0],c['o'][1]-a[...,1]],axis=-1)
def world(c,p):return inverse(c['o'][0]+p[...,0],c['o'][1]-p[...,1])

GREEK={'Eastern Roman Empire':'Βασιλεία Ῥωμαίων','Southern Qi':'Νότιον Τσί','Toba Wei':'Βόρειον Οὐέι',
 'Sasanian Empire':'Σασσανιδικὴ Περσία','Gupta Empire':'Γκούπτα','Visigoths':'Οὐησιγότθοι','Ostrogoths':'Ὀστρογότθοι',
 'Franks':'Φράγκοι','Vandals':'Βάνδαλοι','Burgundians':'Βουργουνδίωνες','Saxons':'Σάξονες','Anglo-Saxons':'Ἀγγλοσάξονες',
 'Suebi':'Σουῆβοι','Axum':'Ἀξώμη','Mauro-Roman Kingdom':'Μαυρορωμαϊκὸν Βασίλειον','Aures Kingdom':'Βασίλειον Αὐρησίου',
 'Himyarite Kingdom':'Ὁμηρῖται','Hephthalites':'Ἐφθαλίται','Lakhmids':'Λαχμίδες','Western Roman Empire':'Δυτικοὶ Ῥωμαῖοι',
 'Koguryo':'Κογκουρυώ','Paekche':'Παίκτσε','Silla':'Σίλλα','Yamato':'Γιαμάτο','Maya states':'Πόλεις Μάγια',
 'Rouran (Ruanruan)':'Ζουράν','Khitan':'Κιτάν','Kumoxi':'Κουμοσί','Makkura':'Μακουρία','Basques':'Βάσκοι',
 'Funan':'Φουνάν','Pyu':'Πιού','Champa':'Τσάμπα','Swedes':'Σουηδοί','Ainu':'Αϊνού','Saami':'Σάμι'}
def greek(s):
    if not s:return ''
    if s in GREEK:return GREEK[s]
    if re.search('[\u0370-\u03ff\u1f00-\u1fff]',s):return s
    s=re.sub(r'\([^)]*\)','',s).strip()
    for a,b in [('Empire','Αὐτοκρατορία'),('Kingdom','Βασίλειον'),('Culture','πολιτισμός'),('culture','πολιτισμός'),('tribes','φυλαί'),('states','πολιτεῖαι'),('peoples','λαοί'),('hunter-gatherers','θηρευταὶ καὶ συλλέκται')]:s=s.replace(a,b)
    out=[];i=0;dig={'th':'θ','ph':'φ','ch':'χ','sh':'σ','kh':'χ','ps':'ψ','oo':'ου','ou':'ου','ai':'αι','ei':'ει','ng':'νγκ','ts':'τσ'}
    abc={'a':'α','b':'β','c':'κ','d':'δ','e':'ε','f':'φ','g':'γ','h':'χ','i':'ι','j':'τζ','k':'κ','l':'λ','m':'μ','n':'ν','o':'ο','p':'π','q':'κ','r':'ρ','s':'σ','t':'τ','u':'ου','v':'β','w':'ου','x':'ξ','y':'υ','z':'ζ'}
    while i<len(s):
        q=s[i:i+2].lower()
        if q in dig:v=dig[q];step=2
        else:v=abc.get(s[i].lower(),s[i]);step=1
        if s[i].isupper():v=v[0].upper()+v[1:]
        out.append(v);i+=step
    return ''.join(out).replace('σ ','ς ').rstrip('σ')+('ς' if s.endswith('s') else '')

for s in D['p500']:s['el']=greek(s['en'])
D['label_language_default']='el'
for c in D['bz17']['city']:c['el']=c['n']
for p in D['bz17']['prov']:p['el']=p['n']
for c in D['eu18']['city']:c['el']=greek(c['lat_name'])
for p in D['eu18']['prov']:p['el']=greek(p['n'])
BYZ={'b0001':'Κωνσταντινούπολις','b0002':'Ἀντιόχεια','b0003':'Ἀλεξάνδρεια','b0004':'Θεσσαλονίκη','b0005':'Ἔφεσος','b0006':'Καισάρεια','b0007':'Ἄγκυρα','b0008':'Νίκαια','b0009':'Ἱεροσόλυμα','b0010':'Δαμασκός','b0011':'Ἔδεσσα','b0012':'Ἄμιδα','b0013':'Τραπεζοῦς','b0014':'Ἡράκλεια','b0015':'Σερδική','b0016':'Ναϊσσός','b0017':'Θεοδοσιούπολις','b0021':'Σαλαμίς','b0022':'Γόρτυνα','b0023':'Ῥόδος'}
airports=[]
for c in cities:
    if not c['k'].startswith('b'):continue
    near=min([p for p in D['bz17']['city'] if p.get('lon') is not None],key=lambda p:(p['lon']-c['lon'])**2+(p['lat']-c['lat'])**2)
    c['el']=BYZ.get(c['k'],near['n']);raw=decode(A['c/'+c['k']+'.json'])
    for i,a in enumerate(raw['air']):
        pt=world(raw,np.array(a['c'])/20);airports.append(dict(n='Ἀερολιμήν · '+c['el']+((' · '+str(i+1)) if i else ''),zh=a['n'],c=pt.tolist(),city=c['k'],kind='airport',el='Ἀερολιμήν · '+c['el']))
    put('c/'+c['k']+'.json',raw)

# Small and medium cities on the Jiaozhou inland and coast corridors.
new=[('qv20_hepu','合浦',109.20,21.67,620000,'广州','合浦郡'),('qv20_xuwen','徐闻',110.1565,20.2611,230000,'广州','合浦郡'),
 ('qv20_guangxin','广信',111.30,23.48,580000,'广州','苍梧郡'),('qv20_l inhe'.replace(' ',''),'临贺',111.55,24.41,260000,'广州','临贺郡'),
 ('qv20_fengyang','封阳',111.7195,23.9942,180000,'广州','临贺郡'),('qv20_gaoyao','高要',112.4532,23.0569,410000,'广州','高要郡'),
 ('qv20_jiaozhi','交趾',105.85,21.03,840000,'交州','交趾郡'),('qv20_zhuyuan','朱鸢',106.06,20.62,260000,'交州','交趾郡'),
 ('qv20_xiyu','西于',105.73,21.24,180000,'交州','交趾郡'),('qv20_quyi','曲易',106.33,20.94,210000,'交州','交趾郡'),
 ('qv20_zhuyai','珠崖',110.35,19.94,480000,'海南','珠崖滨海区'),('qv20_daner','儋耳',109.36,19.52,310000,'海南','儋耳滨海区'),
 ('qv20_qiongdong','琼东',110.47,19.23,210000,'海南','万泉河谷区'),('qv20_lingshui','陵水',110.03,18.50,150000,'海南','陵水滨海区'),
 ('qv20_danshui','淡水津',121.44,25.15,340000,'台湾','淡水河口区'),('qv20_dadu','大肚津',120.55,24.16,280000,'台湾','大肚河口区'),
 ('qv20_taijiang','台江港',120.20,23.01,410000,'台湾','台江潟湖区'),('qv20_lanyang','兰阳津',121.77,24.68,170000,'台湾','兰阳河谷区'),
 ('qv20_hualien','洄澜津',121.59,23.99,160000,'台湾','东纵谷北区'),('qv20_beinan','卑南津',121.12,22.78,190000,'台湾','东纵谷南区')]
land=unpack(D['world']);shapely.prepare(land)
col=['#226d8b','#ad5768','#4f8764']
def make_city(v):
    k,n,lon,lat,p,z,j=v;w=18.;f=forward(lon,lat);o=[float(f[0]-w/2),float(f[1]+w/2)]
    c=dict(k=k,n=n,st='南齐',p=p,kd='规划城市',today='',zhou=z,jun=j,nom='新增交通规划',o=o,w=w,q=20,ax=0,hist='城址',
      zones=[],edge={},dist=[],lake=[],sea=[],riv=[],road=[],bridge=[],rail=[],rst=[],air=[],mn=[],ml=[],ops=[dict(n=n+'交通公署',kind='城市公共交通',scheme='name')],style='gz',xf=[],alt={},lrt=[],xp=[],ports=[],ferries=[],bus=[])
    def local_poly(g):
        return [{'h':0,'r':delta(local(c,np.asarray(p.exterior.coords)))} for p in polygons(g)]
    bbox=box(lon-.14,lat-.12,lon+.14,lat+.12);ground=land.intersection(bbox)
    # Coastal models are clipped to actual atlas land. Route stops are snapped
    # inland rather than putting urban rail through open water.
    pts=[]
    for ang in np.linspace(0,2*np.pi,50):pts.append([9+7*np.cos(ang),9+6*np.sin(ang)])
    reg=Polygon(world(c,np.array(pts))).intersection(land)
    env=local_poly(reg);c['edge']={q:copy.deepcopy(env) for q in ['u','s','p']};c['edge']['x']=[]
    c['zones']=[dict(t=2,r=copy.deepcopy(env),a=round(reg.area*10000,1))]
    c['dist']=[dict(n=n+'城区',c=[180,180],r=copy.deepcopy(env),a=60,pu=p)]
    c['sea']=local_poly(bbox.difference(land))
    for t,(ang,bend) in enumerate([(0,.8),(math.pi/2,-.7),(math.pi/4,.45)]):
        nd=[];path=[]
        for si,d in enumerate(np.linspace(-5.5,5.5,11)):
            q=np.array([9+d*np.cos(ang)+bend*np.sin(d/2),9+d*np.sin(ang)])
            ll=world(c,q)
            if not land.covers(Point(ll)):
                from shapely.ops import nearest_points
                pp=nearest_points(Point(ll),land)[1];q=local(c,np.array([pp.x,pp.y]));q+=(np.array([9,9])-q)*.08
            if abs(d)<.01 and c['mn']:
                ii=next((ii for ii,s in enumerate(c['mn']) if s['n']==n+'城心'),None)
            else:ii=None
            if ii is None:
                suffix=['溪南','兰浦','松麓','竹里','临津','城心','青畴','望津','柳汀','北苑','云岑'][si]
                nm=n+suffix+('东坊' if t==1 and si!=5 else '西坊' if t==2 and si!=5 else '')
                ii=len(c['mn']);c['mn'].append(dict(n=nm,c=np.round(q*20,3).tolist(),l=[],s=[float(q[0]-9),float(9-q[1])]))
            q=np.array(c['mn'][ii]['c'])/20;c['mn'][ii]['l'].append(t);nd.append(ii);path.append(q)
        route=LineString(path);l=dict(n=n+['滨河线','城址线','南北联络线'][t],col=col[t],k='line',s='规划',ring=0,km=round(route.length,1),q=delta(path),nd=nd,op=0,xr=[])
        c['ml'].append(l);c['road'].append(dict(k=1,q=delta(np.array(path)+[0,.13]),width_m=32,sidewalk_m=4,median_m=2))
    c['stats']={'au':42,'as_':68,'ap':90,'p':p,'nst':len(c['mn'])}
    c['metro']=dict(nl=3,km=0,kmp=round(sum(l['km'] for l in c['ml']),1),total_km=round(sum(l['km'] for l in c['ml']),1),nst=len(c['mn']),ring=0,lrtkm=0,xpkm=0)
    c['historical_name']={'display':n,'aliases':[n],'note':'沿用城址或地理名称；新增城市轨道为本图的架空规划。'}
    summary=dict(k=k,n=n,st='南齐',p=p,lon=lon,lat=lat,u=pack(reg.buffer(-.008).buffer(0)),s=pack(reg),pr=pack(reg),px=[],d=[dict(n=n+'城区',c=[lon,lat],r=pack(reg))],dl=[],
      ml=[dict(n=l['n'],col=l['col'],s='规',q=delta(world(c,xy(l['q'])),10000)) for l in c['ml']],ms=[dict(n=s['n'],c=world(c,np.array(s['c'])/20).tolist(),i=len(s['l'])>1,w=len(s['l'])) for s in c['mn']],
      lr=[],xp=[],km=0,nl=3,kind='规划',lst=[],ap=[],ast=[],ports=[],ferries=[],hy=[],historical_name=c['historical_name'],planned_km=c['metro']['kmp'])
    return c,summary
for v in new:
    if any(c['k']==v[0] for c in cities):continue
    raw,s=make_city(v);put('c/'+raw['k']+'.json',raw);cities.append(s)

# Shared world/local intercity corridors; endpoints are named and inspectable.
ROUTES=[]
def route(name,kind,ps,stops=None):
    path=[]
    for a,b in zip(ps,ps[1:]):path.extend([a]+[list(p) for p in G.npts(*a,*b,max(1,int(G.inv(*a,*b)[2]/15000)))])
    path.append(ps[-1]);km=sum(G.inv(*a,*b)[2] for a,b in zip(path,path[1:]))/1000
    ROUTES.append(dict(n=name,kind=kind,q=delta(path,10000),ends=[ps[0],ps[-1]],stops=stops or [],km=round(km,1),status='规划'))
route('交广沿海高速铁路','hsr',[[106.05,21.18],[106.8,21.57],[107.6,21.6],[108.3,21.8],[109.2,21.67],[110.1,21.4],[110.9,21.8],[111.97,21.86],[112.78,22.5],[113.26,23.13]],['龙编','合浦','番禺'])
route('交州—晋兴—始安内陆铁路','rail',[[106.05,21.18],[106.7,21.7],[107.4,22.4],[108.37,22.82],[109.1,23.1],[109.6,24.2],[110.29,25.27]],['龙编','晋兴','始安'])
route('苍梧—临贺—湘州高速铁路','hsr',[[111.3,23.48],[111.72,23.9942],[111.55,24.41],[111.3,25.2],[111.05,25.85],[112.1,26.6],[112.6,27.4],[112.98,28.2]],['广信','封阳','临贺','临湘'])
route('晋兴—合浦货运铁路','rail',[[108.37,22.82],[108.8,22.4],[109.0,22.0],[109.2,21.67]],['晋兴','合浦'])
route('龙编—交趾—朱鸢区域铁路','regional',[[105.73,21.24],[105.85,21.03],[106.06,20.62],[106.33,20.94],[106.05,21.18]],['西于','交趾','朱鸢','曲易','龙编'])
route('交广滨海高速公路','road',[[105.85,21.03],[106.75,21.53],[107.7,21.72],[108.37,22.0],[109.2,21.67],[110.1,21.4],[111.1,21.85],[112.2,22.2],[113.26,23.13]])
route('苍梧—湘江河谷高速公路','road',[[111.3,23.48],[111.55,24.41],[110.9,25.35],[111.6,26.3],[112.2,27.0],[112.98,28.2]])
route('合浦—徐闻半岛铁路','rail',[[109.2,21.67],[109.8,21.45],[110.1,21.0],[110.1565,20.2611]])
route('琼州海峡西桥 · 公铁复合通道','bridge',[[110.025,20.295],[110.04,20.205],[110.08,20.12],[110.16,20.05]],['徐闻西岸','珠崖西岸'])
route('琼州海峡东桥 · 公铁复合通道','bridge',[[110.255,20.32],[110.3,20.23],[110.34,20.12],[110.37,20.045]],['徐闻东岸','珠崖东岸'])
route('海南沿海铁路','rail',[[110.35,19.94],[110.47,19.23],[110.03,18.50],[109.5,18.25],[108.9,18.6],[108.68,19.1],[109.36,19.52],[110.16,20.05],[110.35,19.94]])
route('海南河谷高速公路','road',[[110.35,19.94],[110.1,19.55],[109.75,19.1],[109.5,18.6],[109.5,18.25]])
route('台湾西岸城际铁路','rail',[[121.44,25.15],[121.0,24.8],[120.55,24.16],[120.4,23.6],[120.2,23.01],[120.3,22.6]])
route('台湾东岸铁路','rail',[[121.44,25.15],[121.77,24.68],[121.7,24.35],[121.59,23.99],[121.35,23.5],[121.12,22.78]])
route('台湾西岸高速公路','road',[[121.44,25.15],[121.1,24.8],[120.6,24.16],[120.47,23.6],[120.3,23.01],[120.4,22.6]])
route('罗马色雷斯—安纳托利亚高速公路','road',[[23.32,42.7],[24.75,42.15],[26.56,41.68],[28.98,41.01],[29.73,40.43],[30.4,39.8],[32.86,39.93],[35.48,38.73]])
route('罗马爱琴海东岸铁路','rail',[[29.73,40.43],[29.06,40.18],[28.15,39.66],[27.14,38.42],[27.37,37.95],[27.43,37.03]])
route('罗马黎凡特—埃及高速公路','road',[[36.16,36.2],[36.3,34.73],[36.3,33.51],[35.5,32.0],[34.9,31.5],[34.2,31.1],[32.3,30.7],[31.2,30.05],[29.92,31.2]])
route('罗马巴尔干—希腊铁路','rail',[[23.32,42.7],[23.1,41.3],[22.94,40.64],[22.42,39.64],[22.4,38.9],[23.73,37.98]])

# Islands: urban jurisdictions and valley-based tribal confederations.
islands=[]
def partition(title,bounds,seeds):
    g=land.intersection(box(*bounds));cells=voronoi_diagram(MultiPoint([s[1] for s in seeds]),envelope=g.envelope.buffer(2));out=[]
    for n,p,kind in seeds:
        cell=next(x for x in cells.geoms if x.covers(Point(p)));part=cell.intersection(g)
        label=part.representative_point();out.append(dict(n=n,c=[label.x,label.y],kind=kind,r=pack(part)))
    islands.append(dict(n=title,r=pack(g),areas=out,note='沿河谷与海岸划分的架空自治规划；城名与考古文化参照分列。'))
partition('海南城市与诸峒',[108.45,18.0,111.25,20.22],[('珠崖滨海城域',[110.35,19.94],'city'),('儋耳滨海城域',[109.36,19.52],'city'),('万泉河谷诸峒',[110.3,19.22],'tribe'),('昌化河谷诸峒',[109.15,19.1],'tribe'),('五指山诸峒',[109.65,18.9],'tribe'),('陵水南海诸峒',[110.03,18.5],'tribe')])
partition('台湾城市与部落',[119.95,21.85,122.1,25.45],[('淡水河口诸社',[121.44,25.15],'tribe'),('兰阳河谷诸社',[121.77,24.68],'tribe'),('大肚溪平原诸社',[120.55,24.16],'tribe'),('台江潟湖诸社',[120.2,23.01],'tribe'),('东纵谷北部诸社',[121.5,23.8],'tribe'),('卑南河谷诸社',[121.12,22.78],'tribe'),('中央山地诸社',[121.1,23.7],'tribe')])

D['v20_ext']=dict(routes=ROUTES,airports=airports,islands=islands,japan=D['circ']['jp'],new_city_keys=[v[0] for v in new],
 note='497 年架空交通规划；八道采用含北海道的后世区划参照。',
 sources=['https://icloud.nmp.gov.tw/Classroom/Prehistoric?a=76','https://www.hainanmuseum.org/hnbwgcms/info/597','https://eur-lex.europa.eu/EL/legal-content/summary/united-nations-convention-on-the-law-of-the-sea.html'])

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

# Shared local corridor access for the existing Jiaozhou cities.
for k in ['q0014','q0015','q0016','q0040','q0002']:
    raw=decode(A['c/'+k+'.json']);links=[]
    for l in ROUTES:
        ps=xy(l['q'],10000);lp=local(raw,ps);mask=(lp[:,0]>-8)&(lp[:,0]<raw['w']+8)&(lp[:,1]>-8)&(lp[:,1]<raw['w']+8)
        if mask.sum()<2:continue
        lp=lp[mask];links.append(dict(n=l['n'],kind='regional',col='#8f416f',s='规划',km=l['km'],q=delta(lp),st=[dict(n=raw['n']+'干线换乘',c=np.round(lp[len(lp)//2]*20,3).tolist())]))
    raw['xp'].extend(links);put('c/'+k+'.json',raw)

D['c20']['n']=len(cities);D['c20']['nm']=len(cities)
put('l_city.json',C)
for p,obj in files.items():p.write_text(p.read_text().split('=',1)[0]+'='+dumps(obj)+';')
(OUT/'data/v20_extra.js').write_text('globalThis.__NQA20='+dumps(EXTRA)+';')
PTH.write_text('document.getElementById("data").textContent='+json.dumps(encode(D))+';')
(R.parent/'analysis/v20-world.json').write_text(dumps(D))
(OUT/'extension-v20.json').write_text(json.dumps({'new_cities':len(new),'new_metro_lines':len(new)*3,'routes':[{k:v for k,v in l.items() if k!='q'} for l in ROUTES],'airports':airports,'japan':[x['n'] for x in D['circ']['jp']],'island_areas':sum(len(i['areas']) for i in islands)},ensure_ascii=False,indent=2))
print('Added',len(new),'cities,',len(ROUTES),'corridors,',len(airports),'Roman airports')
