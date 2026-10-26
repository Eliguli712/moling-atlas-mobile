"""Build a script-free, self-contained atlas and replace stale fallback pages."""
from pathlib import Path
from html import escape as esc
import json,re,math
import numpy as np
from shapely.geometry import Polygon,LineString,box
from revise_atlas_v20 import decode,xy
R=Path(__file__).resolve().parent.parent;O=R/'dist';D=decode(json.loads((O/'data/v20r3_d.js').read_text().split('=',1)[1].strip().rstrip(';')));A={}
for p in sorted((O/'data').glob('*a*.js')):A.update(json.loads(p.read_text().split('=',1)[1].strip().rstrip(';')))
C=decode(A['l_city.json'])['city'];H=decode(A['l_hyd.json']);relief=decode(A['global-relief.json'])['tiles']
def svg_map(title,bounds,tag):
 W=1200;Hh=900;minx,miny,maxx,maxy=bounds;cs=math.cos(math.radians((miny+maxy)/2));spanx=(maxx-minx)*cs;spany=maxy-miny;scale=min((W-40)/spanx,(Hh-80)/spany);ox=(W-spanx*scale)/2;oy=(Hh-spany*scale)/2+20;roi=box(*bounds)
 def pt(p):return (ox+(p[0]-minx)*cs*scale,oy+(maxy-p[1])*scale)
 def path(rings,closed=True):
  result=[]
  for q in rings:
   a=xy(q,10000)
   if len(a)<(3 if closed else 2):continue
   g=(Polygon(a).buffer(0) if closed else LineString(a)).intersection(roi)
   for poly in (list(g.geoms) if hasattr(g,'geoms') else [g]):
    if poly.is_empty:continue
    rs=[poly.exterior,*poly.interiors] if poly.geom_type=='Polygon' else [poly]
    for r in rs:
     p=np.array(r.coords);p=np.array([pt(v) for v in p]);result.append('M'+'L'.join(f'{x:.2f},{y:.2f}' for x,y in p)+('Z' if closed else ''))
  return ''.join(result)
 def draw(rings,fill='none',stroke='none',width=1,opacity=1,closed=True):
  d=path(rings,closed)
  if d:out.append(f'<path d="{d}" fill="{fill}" fill-rule="evenodd" stroke="{stroke}" stroke-width="{width}" opacity="{opacity}"/>')
 seen=set()
 def label(ll,text,size=15,col='#243c3a'):
  key=(str(text),round(ll[0],3),round(ll[1],3))
  if key in seen:return
  seen.add(key)
  if not(minx<ll[0]<maxx and miny<ll[1]<maxy):return
  x,y=pt(ll);out.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{col}" stroke="#f8f8f0" stroke-width="3" paint-order="stroke" text-anchor="middle">{esc(str(text))}</text>')
 out=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {Hh}" role="img" aria-label="{esc(title)}"><defs><clipPath id="clip-{tag}"><rect x="8" y="8" width="1184" height="884" rx="12"/></clipPath></defs><g clip-path="url(#clip-{tag})" stroke-linejoin="round" stroke-linecap="round" font-family="system-ui, sans-serif"><rect width="1200" height="900" fill="#cae5ee"/>']
 draw(D['world'],'#f1eee2')
 if tag!='xuanwu':
  for i,s in enumerate(D['p500']):
   rings=s.get('bands',[{}])[1].get('r',[]) if s.get('nm')==1 and len(s.get('bands',[]))>1 else s['r'];col=s.get('col') or ['#ccb3a5','#c9cdae','#d8bfc3','#c8cbdb','#c9d9bc'][i%5]
   draw(rings,col,'#6c786f',.65,.55)
 for island in D['v20_ext']['islands']:
  for i,a in enumerate(island['areas']):draw(a['r'],['#d2dfb4','#e6d0a8','#c0d6cc','#c9c4dd','#d9d7ac','#b9d1df','#debdbe'][i%7],'#698376',1,.9)
 for t in relief:
  if t['e']<=0 or t['e']%500:continue
  l,b,r,u=t['b']
  if r<minx or l>maxx or u<miny or b>maxy:continue
  draw(t['q'],'none','#899776',.55,.45,False)
 for l in H['lake']:
  if minx<l['lon']<maxx and miny<l['lat']<maxy:draw(l['r'],'#a7d4e8','#4889a9',.7)
 for l in D['v20_ext']['routes']:
  if tag=='overview' and l.get('role') not in ['main','freight']:continue
  col='#ae7935' if l['kind']=='road' else '#674783';width=3.4 if l.get('role')=='main' else 1.7 if l.get('role')=='aux' else 2.2
  draw([l['q']],'none','#faf9ed',width+2,1,False);draw([l['q']],'none',col,width,1,False)
  if tag=='liaodong':
   for s in l.get('stations',[]):
    x,y=pt(s['c']);out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.7" fill="#fff" stroke="{col}"/>');label(s['c'],s['n'],15)
 if tag in ['taiwan','hainan']:
  for island in D['v20_ext']['islands']:
   for a in island['areas']:label(a['c'],a['n'],17)
 if tag=='overview':
  for s in D['p500']:
   if not s.get('nm'):label([s.get('lon',0),s.get('lat',0)],s.get('el') or s['zh'],16)
 if tag=='xuanwu':label([118.795,32.086],'玄武湖 · 后湖',30,'#225b7e');label([118.798,32.056],'建康 · 台城',21)
 out.append(f'<rect x="15" y="15" width="1170" height="44" rx="8" fill="#f8f9f1" opacity=".94"/><text x="35" y="44" font-size="23" fill="#253f3b">{esc(title)} · v21</text><text x="25" y="874" font-size="14" fill="#365b67">497 架空世界 · 交通规划 · 海岸与古水域采用参考资料概化</text></g></svg>')
 return ''.join(out)
figures=[]
for title,bounds,tag in [('诸国与交通总览',[15,-5,145,65],'overview'),('辽东主辅铁路与北魏—高句丽货运',[119.7,38.7,126.3,42.7],'liaodong'),('台湾河谷诸社与环岛交通',[119.9,21.8,122.15,25.45],'taiwan'),('海南山地诸峒与沿海城域',[108.45,18.05,111.2,20.3],'hainan'),('建康玄武湖',[118.745,32.05,118.845,32.12],'xuanwu')]:
 svg=svg_map(title,bounds,tag);(O/f'static-{tag}-v21.svg').write_text(svg);figures.append(f'<figure>{svg}<figcaption>{esc(title)}</figcaption></figure>')
summary=f'<p>建武四年（497）设定 · {len(D["zhou"])} 州 · {len(D["jun"])} 郡 · {len(D["xian"])} 县 · {D["c20"]["n"]} 城 · 地铁 {D["c20"]["nm"]} 城</p>'
rows=''.join(f'<tr><td>{esc(c["n"])}</td><td>{esc(c["st"])}</td><td>{c.get("nl",0)}</td><td>{len(c.get("ms",[]))}</td><td>{len(c.get("lr",[]))}</td></tr>' for c in C)
table=f'<details><summary>全部 {len(C)} 城交通规划</summary><div class="table-wrap"><table><thead><tr><th>城市</th><th>所属</th><th>地铁线</th><th>地铁站</th><th>轻轨／电车线</th></tr></thead><tbody>{rows}</tbody></table></div></details>'
body='<p class="fbnote"><b>静态矢量图册 · v21</b>　无需脚本，可缩放查看与打印。</p>'+summary+''.join(figures)+table
style='body{margin:0;background:#edf1ea;color:#253c36;font:16px system-ui,sans-serif}main{max-width:1200px;margin:auto;padding:18px}nav{display:flex;gap:16px;flex-wrap:wrap}a{color:#27695e}figure{margin:20px 0;background:#fafbf6;padding:8px;border-radius:12px}svg{display:block;width:100%;height:auto}figcaption{padding:8px}table{border-collapse:collapse;width:100%}td,th{padding:8px;border-bottom:1px solid #ccd6cc;text-align:left}.table-wrap{overflow:auto}details{padding:12px;background:#fafbf6}'
page='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>南齐静态矢量图册 v21</title><style>'+style+'</style><main><h1>南齐地图 · 静态矢量图册</h1><nav><a href="./index.html">互动地图</a><a href="./README_v21.md">更新说明</a><a href="./static-liaodong-v21.svg" download>辽东铁路矢量图</a></nav>'+body+'</main></html>'
(O/'static.html').write_text(page)
p=O/'index.html';s=p.read_text();a=s.index('<section class="fb" id="fallback"');b=s.index('</section>',a)+10
s=s[:a]+'<section class="fb" id="fallback" aria-label="静态版">'+body+'</section>'+s[b:]
s=s.replace('<a class="rkbtn" href="./static.html">静态图册</a>','')
s=s.replace('<section id="runtime-shortcuts" aria-label="互动快捷入口">','<section id="runtime-shortcuts" aria-label="互动快捷入口"><a class="rkbtn" href="./static.html">静态图册</a>')
p.write_text(s);print('Built self-contained static atlas, 5 current SVG maps and 262 city rows')
