"""Build a checksum-pinned, identical public release for both hosts."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import json,gzip,re,hashlib,io
R=Path(__file__).resolve().parents[1];O=R/'dist';REV='v26-r1';T=R/'analysis-v26';T.mkdir(exist_ok=True)
s=(O/'index.html').read_text();assert 'data/v26_rasters.js' in s
for p in [*O.glob('v20-*.bin'),*O.glob('v21-*.bin'),*O.glob('v22-*.bin'),*O.glob('v23-*.bin'),*O.glob('v26-*.bin')]:p.unlink()
(O/'atlas-mobile.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>南齐世界地图 v26</title><a href="./index.html">打开地图</a><script>location.replace("./index.html"+location.search+location.hash)</script></html>')
notes='''# 南齐世界地图 v26

2026-10-30 · v26-r1。互动、静态与离线版按 SHA-256 清单同步发布。

- 北魏整个政权对象、原始疆界、州郡县与边界线逐对象保持 v25 原样。
- 高句丽全部控制、影响强度层和选中轮廓排除北魏领土；取消上一版重叠主张。北魏境内和龙恢复北魏归属。
- 高句丽外围采用既有 NOAA ETOPO2022 等高线插值的坡度与地形起伏通行代价，再叠加 128 至 4 公里多尺度控制场。海水与北魏境内不可通行，不按经纬线截切边界。
- 扶余、辽东城、安市、建安与卑沙仍位于高句丽范围。广兴争议小区保留北魏归属；接壤缓冲带只画在高句丽一侧。
- 清除渤海对岸与山东岸线附近的离散填色；弱影响层降低不透明度。平面、球面和静态图使用同一组排他边界。
- 保留 v25 的德文、希腊语可折叠世界观、默认希腊语、标签避让、正常铁路样式、地形交通走廊与双色琼州跨海大桥。
- 保留 v25 的球面视口裁切、原生像素影像合成、移动端缓存预算、后台解压暂停及过时任务取消。
- 保留海南、台湾和晋安独立近期规划、秣陵玄武湖避让、城市设施及历史地标资料。

## 验证与来源

validation-v26.json：北魏完整对象一致性、所有高句丽图层与北魏零重叠、控制层嵌套、城址归属、无渤海对岸碎片、曲线采样与脚本语法。render-validation-v26.json：本次浏览器检查。
planning-v26.json：地形控制场来源与参数。现代地形参照用于架空规划，不表示测绘出的历史边界；2 公里为求解插值网格，原始等高线来源分辨率另见元数据。

v25 的道路、地铁、设施与历史地标验证沿用 validation-v25.json、render-validation-v25.json、landmarks-research-v25.json；本次未修改这些交通及设施几何。前期地方规划见 planning-v24.json 与 corridors-v22.json。

静态入口 static.html。iPhone Safari 实机未验证，不承诺固定帧率或零闪退。

© OpenStreetMap contributors（ODbL）；Natural Earth；NOAA ETOPO2022；台湾國土測繪中心；Mapzen Terrain Tiles；地方志与考古来源详见地标资料。
''';(O/'README_v26.md').write_text(notes)
core=['index.html','atlas-mobile.html','manifest.webmanifest','icon-192.png','icon-512.png','static.html']+[p.name for p in sorted(O.glob('static-*-v26.svg'))]+[str(p.relative_to(O)) for p in sorted((O/'data').glob('v26*.js'))]
sw=(O/'sw.js').read_text();a=sw.index('CORE=')+5;b=sw.index(';',a);sw=sw[:a]+json.dumps(core,ensure_ascii=False)+sw[b:];sw=re.sub(r'moling-mobile-v\d+-r\d+-\d+','moling-mobile-v26-r1-20261030',sw);sw=re.sub(r"revision:'v\d+'","revision:'v26'",sw);sw=re.sub(r"rel.startsWith\('data/v\d+'\)","rel.startsWith('data/v26')",sw);sw=sw.replace('if(!r.ok||r.redirected)',"if(!r.ok||new URL(r.url).origin!==self.location.origin)");(O/'sw.js').write_text(sw)
extra=['sw.js','README_v21.md','README_v22.md','README_v23.md','README_v26.md','corridors-v22.json','island-bands-v22.json','validation-v22.json','render-validation-v22.json','revision-v20.json','ring-layout-v20.json','extension-v20.json','connectivity-v20.json','validation-v20.json','world-coordinates-v20.json','bohai-frontier-v20.json','planning-v26.json','validation-v26.json','render-validation-v26.json','planning-v25.json','validation-v25.json','render-validation-v25.json','README_v25.md','landmarks-research-v23.json','landmarks-research-v25.json','planning-v24.json','validation-v24.json','raster-memory-v24.json'];extra=[n for n in extra if (O/n).is_file()]
def inline(m):return '<script>'+(O/m.group(1)).read_text().replace('</script','<\\/script')+'</script>'
single=re.sub(r'<script src="(data/v26[^\"]+\.js)"></script>',inline,s);assert '<script src="data/' not in single
public=core+extra+['final-html.json','final-zip.json']
def parts(kind,data):
 names=[]
 for i,start in enumerate(range(0,len(data),4*1024*1024),1):
  n=f'v26-{kind}-{i:02}.bin';(O/n).write_bytes(data[start:start+4*1024*1024]);names.append(n)
 (O/f'final-{kind}.json').write_text(json.dumps(dict(revision=REV,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),parts=names)));return names
public+=parts('html',gzip.compress(single.encode(),compresslevel=7,mtime=0));buf=io.BytesIO()
with ZipFile(buf,'w',ZIP_DEFLATED,compresslevel=7) as z:
 for n in core+extra:z.write(O/n,n)
public+=parts('zip',buf.getvalue());(T/'moling-atlas-v26.zip').write_bytes(buf.getvalue());public += [p.name for p in sorted(O.glob('广义建康-秣陵_*')) if p.suffix in ['.png','.svg']]+[p.name for p in sorted(O.glob('建康-丹阳_*')) if p.suffix in ['.png','.svg']];public=list(dict.fromkeys(public))
m=dict(revision=REV,source='https://moling-atlas-mobile.eliguli712.chatgpt.site',files=[dict(path=n,bytes=(O/n).stat().st_size,sha256=hashlib.sha256((O/n).read_bytes()).hexdigest()) for n in public]);(R/'asset-manifest-v26.json').write_text(json.dumps(m,ensure_ascii=False,indent=2));total=sum(a['bytes'] for a in m['files']);print('Packaged',len(public),'assets;',total,'bytes;ZIP',len(buf.getvalue()),flush=True)
p=R/'tools/generated-assets.json';gen=json.loads(p.read_text());gen['files']=[f for f in gen['files'] if not re.match(r'dist/(data/v(20|21|22|23|24|25)|v(20|21|22|23|24|25)-)',f['path'])];known={f['path'] for f in gen['files']}
for n in public:
 path='dist/'+n
 if path not in known and ((O/n).stat().st_size>1000000 or n in ['index.html','atlas-mobile.html','static.html']):gen['files'].append(dict(path=path))
p.write_text(json.dumps(gen,ensure_ascii=False,indent=2)+'\n');ignore=(R/'.gitignore').read_text().splitlines()+['/analysis-v26/','/tools/.*.??????']+['/'+f['path'] for f in gen['files']];(R/'.gitignore').write_text('\n'.join(dict.fromkeys(ignore))+'\n');assert total<267000000,total
