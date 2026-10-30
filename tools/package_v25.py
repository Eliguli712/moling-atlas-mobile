"""Build a checksum-pinned, identical public release for both hosts."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import json,gzip,re,hashlib,io
R=Path(__file__).resolve().parents[1];O=R/'dist';REV='v25-r1';T=R/'analysis-v25';T.mkdir(exist_ok=True)
s=(O/'index.html').read_text();assert 'data/v25_rasters.js' in s
for p in [*O.glob('v20-*.bin'),*O.glob('v21-*.bin'),*O.glob('v22-*.bin'),*O.glob('v23-*.bin'),*O.glob('v25-*.bin')]:p.unlink()
(O/'atlas-mobile.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>南齐世界地图 v25</title><a href="./index.html">打开地图</a><script>location.replace("./index.html"+location.search+location.hash)</script></html>')
notes='''# 南齐世界地图 v25

2026-10-30 · v25-r1。互动、静态与离线版按 SHA-256 清单同步发布。

- 北魏整个政权对象、原始疆界、州郡县、边界线与 v24 完全一致，未裁切或重画。
- 仅调整高句丽架空范围，龙城（和龙）、扶余与辽东城镇位于其实际控制区。外围淡色表示较弱影响，沿曲线边缘渐退。北魏主张与高句丽控制可重叠，图例明确说明。
- 保留约 1,246 km² 的广兴小框区，按北魏归属标为争议地区。棕色虚线及淡色带表示直接接壤缓冲区，不改北魏原界。
- 前置德文与希腊语世界观可折叠，首次默认收起。图例首次默认展开，解释架空线路、特别自由市、ΑΟΖ（Αποκλειστική Οικονομική Ζώνη）、影响力与争议区。
- 普速铁路与内地统一为灰色实线，高铁维持紫色白芯。辽东主辅与跨境货运沿既有地形走廊；琼州西桥琥珀色，东桥蓝色。
- 城市名称先占位，次级线路端点与区划避让。移动端缩远时隐藏长线路名与机场名，完整路线见图例。
- 球面 Canvas 回退改为可见视口网格，高倍放大仍覆盖视口。影像先合成到原生像素画布再整体叠加，消除网格重复加深接缝。
- 正射和倾斜透视均剔除视口外几何；网格仅缓存当前相机。后台暂停新解压与影像解码，切城时淘汰失效请求。保留移动端 24 MiB 几何、24 MP 影像预算及单并发。
- 保留海南四城、台湾六城与晋安的独立近期规划，共 13 条新增线路。小城市优先轻轨、公交，秣陵地铁避开玄武湖，海岸环路和海岛共享平滑边界沿用地理修订。
- 262 城保留购物、餐饮、影院、创作工坊、三维打印、公园与河流特别区；随新版河流移动兰阳、卑南三处设施到邻近可建设地块。
- 11 项独立历史地标资料含年代、近似位置与来源；更新台城、石头城、晋安西湖、华林寺、洛阳阊阖门及古阳洞早期阶段。后世建筑明确标注，历史模式隐藏现代设施和后世地标。

## 验证与来源

validation-v25.json：北魏逐对象一致性、龙城/扶余/辽东覆盖、争议小区、262 城道路海湖检查、地铁避湖、近期线路、海岛无缝区划。
render-validation-v25.json：本次投影网格、解压队列、标签与浏览器检查的实际结果。
planning-v25.json：政治设定和设施调整。landmarks-research-v25.json：历史来源与位置误差。

现代交通、设施及政治范围为架空规划；地形和城址提供参照。地标为城市尺度近似索引，不表示古建筑轮廓。iPhone Safari 实机未验证，不承诺固定帧率或零闪退。

前期地方交通见 planning-v24.json、validation-v24.json、raster-memory-v24.json；走廊来源见 corridors-v22.json。静态入口 static.html。

© OpenStreetMap contributors（ODbL）；Natural Earth；台湾國土測繪中心；Mapzen Terrain Tiles；地方志与考古来源详见地标资料。
''';(O/'README_v25.md').write_text(notes)
core=['index.html','atlas-mobile.html','manifest.webmanifest','icon-192.png','icon-512.png','static.html']+[p.name for p in sorted(O.glob('static-*-v25.svg'))]+[str(p.relative_to(O)) for p in sorted((O/'data').glob('v25*.js'))]
sw=(O/'sw.js').read_text();a=sw.index('CORE=')+5;b=sw.index(';',a);sw=sw[:a]+json.dumps(core,ensure_ascii=False)+sw[b:];sw=re.sub(r'moling-mobile-v\d+-r\d+-\d+','moling-mobile-v25-r1-20261030',sw);sw=re.sub(r"revision:'v\d+'","revision:'v25'",sw);sw=re.sub(r"rel.startsWith\('data/v\d+'\)","rel.startsWith('data/v25')",sw);sw=sw.replace('if(!r.ok||r.redirected)',"if(!r.ok||new URL(r.url).origin!==self.location.origin)");(O/'sw.js').write_text(sw)
extra=['sw.js','README_v21.md','README_v22.md','README_v23.md','README_v25.md','corridors-v22.json','island-bands-v22.json','validation-v22.json','render-validation-v22.json','revision-v20.json','ring-layout-v20.json','extension-v20.json','connectivity-v20.json','validation-v20.json','world-coordinates-v20.json','bohai-frontier-v20.json','planning-v25.json','validation-v25.json','render-validation-v25.json','landmarks-research-v23.json','landmarks-research-v25.json','planning-v24.json','validation-v24.json','raster-memory-v24.json'];extra=[n for n in extra if (O/n).is_file()]
def inline(m):return '<script>'+(O/m.group(1)).read_text().replace('</script','<\\/script')+'</script>'
single=re.sub(r'<script src="(data/v25[^\"]+\.js)"></script>',inline,s);assert '<script src="data/' not in single
public=core+extra+['final-html.json','final-zip.json']
def parts(kind,data):
 names=[]
 for i,start in enumerate(range(0,len(data),4*1024*1024),1):
  n=f'v25-{kind}-{i:02}.bin';(O/n).write_bytes(data[start:start+4*1024*1024]);names.append(n)
 (O/f'final-{kind}.json').write_text(json.dumps(dict(revision=REV,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),parts=names)));return names
public+=parts('html',gzip.compress(single.encode(),compresslevel=7,mtime=0));buf=io.BytesIO()
with ZipFile(buf,'w',ZIP_DEFLATED,compresslevel=7) as z:
 for n in core+extra:z.write(O/n,n)
public+=parts('zip',buf.getvalue());(T/'moling-atlas-v25.zip').write_bytes(buf.getvalue());public += [p.name for p in sorted(O.glob('广义建康-秣陵_*')) if p.suffix in ['.png','.svg']]+[p.name for p in sorted(O.glob('建康-丹阳_*')) if p.suffix in ['.png','.svg']];public=list(dict.fromkeys(public))
m=dict(revision=REV,source='https://moling-atlas-mobile.eliguli712.chatgpt.site',files=[dict(path=n,bytes=(O/n).stat().st_size,sha256=hashlib.sha256((O/n).read_bytes()).hexdigest()) for n in public]);(R/'asset-manifest-v25.json').write_text(json.dumps(m,ensure_ascii=False,indent=2));total=sum(a['bytes'] for a in m['files']);print('Packaged',len(public),'assets;',total,'bytes;ZIP',len(buf.getvalue()),flush=True)
p=R/'tools/generated-assets.json';gen=json.loads(p.read_text());gen['files']=[f for f in gen['files'] if not re.match(r'dist/(data/v(20|21|22|23|24|25)|v(20|21|22|23|24|25)-)',f['path'])];known={f['path'] for f in gen['files']}
for n in public:
 path='dist/'+n
 if path not in known and ((O/n).stat().st_size>1000000 or n in ['index.html','atlas-mobile.html','static.html']):gen['files'].append(dict(path=path))
p.write_text(json.dumps(gen,ensure_ascii=False,indent=2)+'\n');ignore=(R/'.gitignore').read_text().splitlines()+['/analysis-v25/','/tools/.*.??????']+['/'+f['path'] for f in gen['files']];(R/'.gitignore').write_text('\n'.join(dict.fromkeys(ignore))+'\n');assert total<267000000,total
