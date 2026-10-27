"""Install the additional independently sourced city landmarks into v23 assets."""
import json,pickle,numpy as np
from pathlib import Path
import revise_atlas_v23 as m
p=m.R/'tools/landmarks-research-v23.json';r=json.loads(p.read_text());more=[dict(city_key='w0549be',n='龙门石窟 · 早期造像区',el='Σπήλαια Λονγκμέν · πρώιμη φάση',c=[112.478,34.559],status='北魏起建的石窟遗址／后续历代扩建',period='493年起营造；497年仅作早期阶段参照',basis='UNESCO申报材料记载493年开凿。后世大窟与大像不作为497年原貌。',accuracy_m=1000,sources=[dict(title='UNESCO：Longmen Grottoes nomination',url='https://whc.unesco.org/uploads/nominations/1003.pdf')]),dict(city_key='wf466e6',n='汉长安未央宫遗址',el='Ανάκτορο Ουεϊγιάνγκ · αρχαιολογικός χώρος',c=[108.861,34.304],status='汉代宫城考古遗址',period='西汉宫城遗址；497年作为历史遗迹参照',basis='UNESCO丝路遗产点包含西汉长安未央宫遗址；不推定497年完整宫殿仍然存续。',accuracy_m=1200,sources=[dict(title='UNESCO：Silk Roads property component maps',url='https://whc.unesco.org/en/list/1442/maps/')]),dict(city_key='k0008',n='月城宫城遗址',el='Ανακτορικός χώρος Ουόλσονγκ',c=[129.221,35.83],status='新罗宫城考古遗址',period='新罗历史城址；遗存与考古材料跨多个时期',basis='UNESCO庆州历史区月城片区包含宫城遗址。图点作城市尺度历史参照，不补绘后世天文台或宫殿轮廓。',accuracy_m=700,sources=[dict(title='UNESCO：Gyeongju Historic Areas',url='https://whc.unesco.org/en/list/976/')])]
for a in more:
 if not any(b['city_key']==a['city_key'] for b in r['landmarks']):r['landmarks'].append(a)
p.write_text(json.dumps(r,ensure_ascii=False,indent=2));cs=pickle.load(open(m.T/'cities.pkl','rb'));changed={}
for a in more:
 c=cs[a['city_key']];pos=m.local(c,a['c'])
 if np.all(pos>=0) and np.all(pos<=c['w']) and not any(b['n']==a['n'] for b in c['amenities_v23']):c['amenities_v23'].insert(0,{**a,'c':(pos*20).round(3).tolist(),'r':[],'kind':'historic_site','services':['历史地标','考古与城市记忆']});changed['c/'+c['k']+'.json']=m.encode(c)
for p in (m.O/'data').glob('v23_a*.js'):
 prefix,body=p.read_text().split('=',1);d=json.loads(body.strip().rstrip(';'));hit=set(changed)&set(d)
 if 'l_city.json' in d:
  c=m.decode(d['l_city.json'])
  for s in c['city']:
   if 'c/'+s['k']+'.json' in changed:s['amenities23']=[{k:v for k,v in a.items() if k not in ['c','r']} for a in cs[s['k']]['amenities_v23']]
  d['l_city.json']=m.encode(c);hit.add('l_city.json')
 if hit:
  for k in hit:
   if k in changed:d[k]=changed[k]
  p.write_text(prefix+'='+m.dumps(d)+';')
pickle.dump(cs,open(m.T/'cities.pkl','wb'));print('Independent landmark sources',len(r['landmarks']),'new installed',len(changed))
