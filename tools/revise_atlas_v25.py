"""v25: freeze Wei; adjust fictional Goguryeo control, influence and dispute."""
from atlas25_support import *
from atlas24_support import planning_namespace
import copy,hashlib,math
import numpy as np,shapely
from shapely.geometry import Polygon,LineString,Point,box
from shapely.ops import unary_union
from shapely.affinity import translate
from scipy.interpolate import CubicSpline
D,A,FILES,C=baseline25();N=planning_namespace(D);geo=N['geo'];poly=N['poly'];local=N['local'];Plan=N['Plan'];parts=N['parts']
def sha(x):return hashlib.sha256(dumps(x).encode()).hexdigest()
wei=next(s for s in D['p500'] if s['en']=='Toba Wei');gog=next(s for s in D['p500'] if s['en']=='Koguryo')
frozen=dict(wei=sha(wei),wei17=sha(D['wei17']),weiline=sha(D['L']['weiline']),wei_nominal=sha(D.get('wei_nominal_v15')))
roi=box(118.5,37.2,134,46);land=unary_union([poly(q,10000).intersection(roi) for q in D['world'] if len(q)>5 and poly(q,10000).intersects(roi)])
old=geo(gog.get('fb') or gog['r'],10000)
# Regional anchors follow the supplied red sketch and retained terrain corridors.
anchor=np.array([[119.8,40.0],[119.83,40.35],[119.76,40.95],[119.65,41.55],[119.9,42.05],[120.22,42.55],[120.1,43.15],[120.65,43.85],[121.35,44.35],[122.15,44.65],[123.1,44.65],[124.15,44.7],[125.25,44.55],[126.4,44.4],[127.55,44.2],[128.75,44.25],[130,44.25],[131.35,43.95],[132,43.55]])
ts=np.r_[0,np.cumsum(np.linalg.norm(np.diff(anchor,axis=0)*[.75,1],axis=1))];t=np.linspace(0,ts[-1],int(ts[-1]/.012)+1);a=CubicSpline(ts,anchor,axis=0,bc_type='natural')(t);v=np.gradient(a,axis=0);norm=np.column_stack([-v[:,1],v[:,0]]);norm/=np.linalg.norm(norm,axis=1)[:,None];rng=np.random.default_rng(49725);noise=np.zeros(len(t))
for scale,amp in [(1.1,.023),(.36,.012),(.12,.005),(.035,.0016)]:
 knots=np.arange(0,ts[-1]+scale,scale);noise+=np.interp(t,knots,rng.normal(0,amp,len(knots)))
a+=norm*noise[:,None]*np.sin(np.linspace(0,np.pi,len(t)))[:,None]
cap=Polygon(np.vstack([a,[134,43.4],[134,35],[119,35],a[0]])).intersection(land)
outer=shapely.set_precision(unary_union([old,cap]).buffer(0),.0001)
county=next(x for x in D['wei17']['xian'] if x['n']=='广兴' and x.get('z')=='营州')
dispute=geo(county['r'],10000).intersection(outer).buffer(0);assert not dispute.is_empty and area(dispute)<4000
# Peripheral weak influence follows the curved north/west frontier, never a
# latitude cut or rectangular administrative strip. The coast remains exact.
peripheral=LineString(a).buffer(.19,join_style='round').intersection(outer)
core=outer.difference(peripheral.union(dispute)).buffer(0)
urban=unary_union([Point(lo,la).buffer(.23) for lo,la in [(120.4508,41.5801),(124.85,43.45),(123.1727,41.2578),(122.85,40.7),(122.45,40.4),(121.95,39.15),(126.19,41.12),(125.785,39.128)]]).intersection(core)
weak=outer.difference(core.union(dispute));weigeo=geo(wei['r'],10000);overlap=weigeo.intersection(outer).difference(dispute)
contact=weigeo.boundary.intersection(core.buffer(.008)).intersection(box(119.0,39.6,123.6,43.8)).difference(land.boundary.buffer(.035));assert contact.length>.02
buffer=contact.buffer(.085).intersection(land).difference(dispute)
for b in gog['bands']:
 threshold=b['t'];g=outer if threshold<=.15 else core if threshold<=.3 else core.buffer(-.07).union(urban).intersection(core) if threshold<=.45 else urban.buffer(.13).intersection(core) if threshold<=.6 else urban
 b['r']=pack(g);b['f']=b['r']
gog.update(r=pack(outer),fb=pack(outer),a=area(core),a2=area(outer),asph=area(core),a1=area(urban))
gog['intro']+=' v25 架空设定：龙城（和龙）、扶余及辽东位于高句丽范围内；北魏原疆界保持原样。广兴小框区由北魏控制、双方争议；外围淡色表示较弱影响。'
gog['control_v25']={'actual_area_km2':area(core),'influence_area_km2':area(weak),'extent_area_km2':area(outer),'dispute_area_km2':area(dispute),'note':'用户指定的架空范围；主张可重叠，北魏原疆界未裁切。'}
if not any(c['n'].startswith('龙城') or c['n']=='和龙' for c in gog['cities']):gog['cities'].append(dict(n='龙城（和龙）',lon=120.4508,lat=41.5801,w=1))
center=list(dispute.representative_point().coords[0]);buffer_c=list(contact.interpolate(.5,normalized=True).coords[0])
D['v25']=dict(revision='v25-r1',wei_frozen=frozen,frontier=dict(extent_r=pack(outer),control_r=pack(core),urban_r=pack(urban),influence_r=pack(weak),overlap_r=pack(overlap),dispute_r=pack(dispute),dispute_c=center,dispute_zh='北魏·广兴争议区',dispute_el='Βόρειον Οὐέι · αμφισβητούμενη ζώνη',dispute_owner='北魏',dispute_basis='保留既有营州广兴县模型作为参考小框；架空主张重叠，非史实国界复原',contact_q=[delta(g.coords,10000) for g in parts(contact)],buffer_r=pack(buffer),buffer_c=buffer_c,buffer_zh='北魏—高句丽接壤缓冲区',buffer_el='Ζώνη ασφαλείας Ουέι–Κογκουρυώ',buffer_note='接壤线两侧约10—20公里示意带；不改变北魏既有疆界。',reference='用户红线参考图；保留现代地形/海岸和既有县界参照。',**gog['control_v25']))
key='wdf268c';raw=decode(A['c/'+key+'.json']);raw['st']='高句丽';raw['nom']='v25 架空实际控制：高句丽；北魏原疆界主张保留，广兴小框区按北魏争议地区标注。';A['c/'+key+'.json']=encode(raw)
s=next(c for c in C['city'] if c['k']==key);s['st']='高句丽';s['pol']='Koguryo'
# Historical references keep approximate indices separate from modern facilities.
research=copy.deepcopy(json.loads((R/'tools/landmarks-research-v23.json').read_text()));research.update(revision='v25',researched_on='2026-10-30')
for q in research['landmarks']:
 if q['city_key']=='q0000' and '台城' in q['n']:
  q.update(n='建康台城宫城遗址',el='Ανακτορικός χώρος της Τζιανκάνγκ',c=[118.799,32.042],earliest_year=330,period='330年起；东晋、南朝宫城遗址',basis='宫城历史和遗存依据地方志；近似索引不等同于玄武湖南岸明城墙。');q['sources']=[dict(title='南京市地方志：千年沧桑话台城',url='https://dfz.nanjing.gov.cn/gzdt/202502/t20250207_5069953.html')]
 if q['city_key']=='w0549be' and '龙门' in q['n']:
  q.update(n='龙门古阳洞·早期造像阶段',el='Σπήλαιο Γκουγιάνγκ · πρώιμες λαξεύσεις',earliest_year=493,period='493年起凿，后续持续至6世纪',basis='497年表示起凿后的早期阶段；不将后期龛像或唐代奉先寺并入同期现状。');q.setdefault('sources',[]).append(dict(title='中央研究院：龙门石窟古阳洞',url='https://buddhism.ascdc.sinica.edu.tw/buddhism/layer1.php?id1=G04030000'))
research['landmarks'].extend([
 dict(city_key='q0065',n='严高西湖历史水利区',el='Δυτική Λίμνη · ιστορικό υδραυλικό τοπίο',c=[119.283,26.096],earliest_year=282,period='西晋282年起源，后世持续整治',basis='方志记严高筑子城并开东西湖；现今湖岸、公园与桥亭另属后世景观。',sources=[dict(title='福州市政府·方志委：晋安郡首任太守——严高',url='https://www.fuzhou.gov.cn/zgfzzt/zjrc/mdfc/mdrj/201811/t20181112_2674287.htm')]),
 dict(city_key='q0065',n='华林寺大殿·后世参照',el='Ναός Χουαλίν · μεταγενέστερο μνημείο',c=[119.292,26.104],earliest_year=964,later_reference=True,period='964年创建，明清修缮',basis='后世历史木构参照，497年历史场景中不显示；现代设施独立标为架空规划。',sources=[dict(title='福州市政府·方志委：名人与华林寺',url='https://www.fuzhou.gov.cn/zgfzzt/zjrc/mdfc/mdrj/202409/t20240925_4899139.htm')]),
 dict(city_key='q0000',n='石头城遗址·清凉山考古区',el='Αρχαιολογικός χώρος Σιτόουτσενγκ',c=[118.753,32.054],earliest_year=212,period='史载212年筑城，考古确认六朝遗存',basis='清凉山考古范围近似索引，不将现存明代城墙或现代博物馆当作六朝原构。',sources=[dict(title='南京大学：解开石头城千年之谜',url='https://www.nju.edu.cn/info/1056/336061.htm')]),
 dict(city_key='w0549be',n='汉魏洛阳宫城阊阖门遗址',el='Πύλη Τσανγκχέ της αρχαίας Λουογιάνγκ',c=[112.625,34.731],earliest_year=226,period='曹魏始建，西晋及北魏沿用增修',basis='考古证实曹魏夯土基址与后期增修；不复原未经分期的完整北魏门楼。',sources=[dict(title='钱国祥：汉魏洛阳故城居中宫城制度考',url='https://www.nopss.gov.cn/n1/2018/0704/c373410-30125781.html')])])
for q in research['landmarks']:q.setdefault('accuracy_note','WGS84城市尺度近似索引，误差约0.4—1.2公里；不表示建筑轮廓。')
for ck in ['q0000','q0065','w0549be']:
 c=decode(A['c/'+ck+'.json']);existing=[a for a in c.get('amenities_v23',[]) if a['kind']!='historic_site' or a.get('n','').endswith('史载城址参照')]
 for q in research['landmarks']:
  if q['city_key']!=ck:continue
  loc=local(c,q['c'])
  if not np.all((loc>=0)&(loc<=c['w'])):continue
  existing.insert(0,{**q,'c':(loc*20).round(3).tolist(),'r':[],'kind':'historic_site','services':['历史地标','城市记忆'],'status':'后世历史参照' if q.get('later_reference') else '史载遗址／近似索引'})
 c['amenities_v23']=existing;A['c/'+ck+'.json']=encode(c);cs=next(s for s in C['city'] if s['k']==ck);cs['amenities23']=[{k:v for k,v in a.items() if k not in ['r','c']} for a in existing]
facility_fixes=[]
for cs in C['city']:
 if cs['k'] not in ['qv20_lanyang','qv20_beinan']:continue
 c=decode(A['c/'+cs['k']+'.json']);p=Plan(c);changed=False
 for a in c['amenities_v23']:
  if a['status']!='架空规划' or a['kind'] in ['park','suburban_park','river_district']:continue
  at=np.array(a['c'])/20
  if p.buildable.buffer(.002).covers(Point(at)):continue
  target=p.snap(at,build=True);shift=target-at;a['c']=(target*20).round(3).tolist();a['r']=N['localrings'](translate(geo(a.get('r',[])),*shift).intersection(p.buildable));a['basis']+='；v25随新版河流移至相邻可建设地块。';changed=True;facility_fixes.append(dict(city=c['k'],facility=a['n'],moved_m=round(np.linalg.norm(shift)*1000)))
 if changed:A['c/'+c['k']+'.json']=encode(c)
A['l_city.json']=encode(C)
assert frozen==dict(wei=sha(wei),wei17=sha(D['wei17']),weiline=sha(D['L']['weiline']),wei_nominal=sha(D.get('wei_nominal_v15')))
for name,(prefix,data) in FILES.items():
 for key in data:
  if key in A:data[key]=A[key]
 (O/'data'/name.replace('v24','v25')).write_text(prefix+'='+dumps(data)+';')
(O/'data/v25_d.js').write_text('document.getElementById("data").textContent='+json.dumps(encode(D))+';');(O/'data/v25_rasters.js').write_bytes((O/'data/v24_rasters.js').read_bytes())
for p in [R/'tools/landmarks-research-v25.json',O/'landmarks-research-v25.json']:p.write_text(json.dumps(research,ensure_ascii=False,indent=2))
report=dict(revision='v25-r1',wei_frozen=frozen,wei_unchanged=True,frontier={k:v for k,v in D['v25']['frontier'].items() if not k.endswith('_r') and k!='contact_q'},historical_landmarks=len(research['landmarks']),city_count=len(C['city']),facility_relocations=facility_fixes,retained_v24_local_transit=['海南四城','台湾六城','晋安两条新线'])
(O/'planning-v25.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));pickle.dump((D,A,FILES,C),open(T/'result.pkl','wb'));print('Built v25 data; Wei unchanged; historical landmarks',len(research['landmarks']),'facility fixes',len(facility_fixes),flush=True)
