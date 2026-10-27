"""Create an immutable, checksum-pinned v23 distribution for both hosts."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import json,gzip,re,hashlib,io
REV='v23-r2'
R=Path(__file__).resolve().parents[1];O=R/'dist';deliver=R/'analysis-v23';deliver.mkdir(exist_ok=True)
s=(O/'index.html').read_text().replace('v=23-r1','v=23-r2').replace('v22 完整包','v23 完整包').replace('README_v22.md','README_v23.md').replace('南齐世界地图_v22','南齐世界地图_v23');(O/'index.html').write_text(s)
for p in list(O.glob('v20-*.bin'))+list(O.glob('v21-*.bin'))+list(O.glob('v22-*.bin'))+list(O.glob('v23-*.bin')):p.unlink()
(O/'atlas-mobile.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>南齐世界地图 v23</title><a href="./index.html">打开地图</a><script>location.replace("./index.html"+location.search+location.hash)</script></html>')
core=['index.html','atlas-mobile.html','manifest.webmanifest','icon-192.png','icon-512.png','static.html']+[p.name for p in sorted(O.glob('static-*-v23.svg'))]+[str(p.relative_to(O)) for p in sorted((O/'data').glob('v23*.js'))]
sw=(O/'sw.js').read_text();a=sw.index('CORE=')+5;b=sw.index(';',a);sw=sw[:a]+json.dumps(core,ensure_ascii=False)+sw[b:];sw=re.sub('moling-mobile-v[0-9]+-r[0-9]+-[0-9]+','moling-mobile-'+REV+'-20261027',sw);sw=sw.replace("revision:'v22'","revision:'v23'").replace("rel.startsWith('data/v22')","rel.startsWith('data/v23')");(O/'sw.js').write_text(sw)
notes='''# 南齐世界地图 v23

2026-10-27 更新（v23-r2）。互动地图、静态图册与离线包使用同一份 SHA-256 清单，两站同步发布。

- 地图前加入德文与希腊语架空世界观。新用户默认展开图例，说明城市轨道颜色、运营状态、特别自由市及 Αποκλειστική Οικονομική Ζώνη（ΑΟΖ）。
- 普速、高速铁路统一内地符号。琼州海峡西桥为琥珀色，东桥为蓝色。
- 东北按用户指定的架空设定调整：龙城、扶余、辽东全境归高句丽，北魏直接接壤，绘制两侧缓冲区。地形边界以辽西山地与松辽平原过渡带概化，非497年史实复原。
- 262 城按各自海陆、水系与高程筛选道路。海上环路改为陆上通道或开放沿岸道路；现行地铁避开湖面，玄武湖附近重新绕行。分隔岛屿间未落实跨海工程的线段分开显示。
- 晋安（侯官）新增子城线和闽江北岸线，连接西湖、乌山与滨江走廊，配合原晋安—马江地铁、轻轨与邻近交通。
- 每城补入城市生活规划：购物、餐饮、影院、创作工坊、三维打印、城市/郊野公园和河流特别区。按自身街区和轨道节点选址；262 个城市采用独立的街网尺度与取向种子。
- 历史城名/城址附原有文献来源，独立查证的古建筑/遗址另附年代、来源与近似坐标；后世重建、现代架空设施明确区分。未推定古建筑轮廓。
- 海南、台湾内部区划共享平滑边界，保留详细海岸和完整覆盖。
- 移动端采用视口防碰撞、标签分级，线路徽标有空位才显示。球面路径裁剪到视口；移动端球面几何缓存预算24MiB，城市模型淘汰时同步释放GPU资源。上下文失效回退到Canvas，继续保留实时清晰的符号和轨道。

- r2 修正快捷视图后的球形按钮状态，切换投影保留当前中心与比例；即时绘制取代大尺寸过渡截图。球面先剔除视口外轮廓，再创建可见轮廓坐标缓存，降低高倍缩放时的运算和内存占用。

## 资料与验证

现代城市设施、国界与交通工程属于架空世界设定，不作为497年史实复原或施工方案。历史位置为城市尺度参照。

validation-v23.json：逐城道路/湖面相交、设施海陆、岛内区划覆盖与东北归属检查。planning-v23.json：逐城修订数量。landmarks-research-v23.json：独立查证的历史地标。

交通资料继续使用 © OpenStreetMap contributors（ODbL）、Natural Earth 公共领域和台湾國土測繪中心开放道路资料；详细来源见 corridors-v22.json。静态版入口 static.html。旧版说明 README_v22.md。
''';(O/'README_v23.md').write_text(notes)
(O/'landmarks-research-v23.json').write_bytes((R/'tools/landmarks-research-v23.json').read_bytes())
extra=['sw.js','README_v21.md','README_v22.md','README_v23.md','corridors-v22.json','island-bands-v22.json','validation-v22.json','render-validation-v22.json','revision-v20.json','ring-layout-v20.json','extension-v20.json','connectivity-v20.json','validation-v20.json','world-coordinates-v20.json','bohai-frontier-v20.json','planning-v23.json','validation-v23.json','render-validation-v23.json','landmarks-research-v23.json'];extra=[n for n in extra if (O/n).is_file()]
def inline(m):return '<script>'+(O/m.group(1)).read_text().replace('</script','<\\/script')+'</script>'
single=re.sub(r'<script src="(data/v23[^\"]+\.js)"></script>',inline,s);assert '<script src="data/' not in single
public=core+extra+['final-html.json','final-zip.json']
def parts(kind,data):
 names=[]
 for i,start in enumerate(range(0,len(data),4*1024*1024),1):
  n=f'v23-{kind}-{i:02}.bin';(O/n).write_bytes(data[start:start+4*1024*1024]);names.append(n)
 (O/f'final-{kind}.json').write_text(json.dumps(dict(revision=REV,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),parts=names)));return names
public+=parts('html',gzip.compress(single.encode(),compresslevel=7,mtime=0));buf=io.BytesIO()
with ZipFile(buf,'w',ZIP_DEFLATED,compresslevel=7) as z:
 for n in core+extra:z.write(O/n,n)
public+=parts('zip',buf.getvalue());(deliver/'moling-atlas-v23.zip').write_bytes(buf.getvalue())
public+=[p.name for p in sorted(O.glob('广义建康-秣陵_*')) if p.suffix in ['.svg','.png']];public+=[p.name for p in sorted(O.glob('建康-丹阳_*')) if p.suffix in ['.svg','.png']];public=list(dict.fromkeys(public));manifest=dict(revision=REV,source='https://moling-atlas-mobile.eliguli712.chatgpt.site',files=[dict(path=n,bytes=(O/n).stat().st_size,sha256=hashlib.sha256((O/n).read_bytes()).hexdigest()) for n in public]);(R/'asset-manifest-v23.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));total=sum(a['bytes'] for a in manifest['files']);print('Packaged',len(public),'assets,',total,'bytes; ZIP',len(buf.getvalue()),flush=True)
p=R/'tools/generated-assets.json';m=json.loads(p.read_text());m['files']=[f for f in m['files'] if not f['path'].startswith(('dist/data/v20','dist/data/v21','dist/data/v22','dist/data/v23','dist/v20-','dist/v21-','dist/v22-','dist/v23-'))];known={f['path'] for f in m['files']}
for n in public:
 path='dist/'+n
 if path not in known and ((O/n).stat().st_size>1000000 or n in ['index.html','atlas-mobile.html']):m['files'].append(dict(path=path))
p.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
with (R/'.gitignore').open('a') as f:
 for n in public:
  if any(v['path']=='dist/'+n for v in m['files']):f.write('\n/dist/'+n)
assert total<267000000,total
