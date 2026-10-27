"""Build a checksum-pinned, identical public release for both hosts."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import json,gzip,re,hashlib,io
R=Path(__file__).resolve().parents[1];O=R/'dist';REV='v24-r1';T=R/'analysis-v24';T.mkdir(exist_ok=True)
s=(O/'index.html').read_text();assert 'data/v24_rasters.js' in s
for p in [*O.glob('v20-*.bin'),*O.glob('v21-*.bin'),*O.glob('v22-*.bin'),*O.glob('v23-*.bin'),*O.glob('v24-*.bin')]:p.unlink()
(O/'atlas-mobile.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>南齐世界地图 v24</title><a href="./index.html">打开地图</a><script>location.replace("./index.html"+location.search+location.hash)</script></html>')
notes='''# 南齐世界地图 v24

2026-10-27 更新（v24-r1）。互动地图、静态图册和离线包使用同一 SHA-256 清单，两站同步发布。

- 北魏东北外界、州郡县及原始边界线精确恢复到 v22；和龙恢复北魏归属。其他地区的交通、水系与修订保持连续。
- 德文、希腊语世界观可折叠，首次默认收起，记忆展开选择。静态页同样可折叠。
- 海南四城与台湾六城分别采用海岸、河流、平原、山麓及既有道路走廊规划近期轨道。人口较小城市优先轻轨与公交；珠崖、淡水、台江保留有限地铁骨干。新线全部标明规划，取消模板式环线。
- 晋安新增东山—鼓山山麓线与北站接驳支线，沿建成区低地连接，保留既有线网。两线在北站接驳节点联系。
- 采用 Mapzen Terrarium z11 高程、OpenStreetMap 干道及河流、保留的台湾开放道路走廊。新线检查海陆、湖泊、站位和地形；轻轨优先缓坡。
- 首屏按视口选择整幅地形影像层级，保留原始最高分辨率影像，清晰图整幅替换；不再预解码全部十幅原图和影像金字塔。
- 移动端数据与影像解码各限制并发 1，桌面为 2；缓存与视口挂钩。关闭城市、切入后台时释放画布、城市、地形及 GPU 资源。请求序号防止旧城市在快速切换后覆盖当前视图。
- 球面保留视口裁剪，停用双 4096×2048 CPU 纹理路径；几何缓存移动端上限 24 MiB。主页面移除隐藏的巨型静态 SVG，独立静态图册保持完整。

## 来源与验证

现代设施、交通与政治边界是架空世界规划；地形和城址提供参照，未作地质、客流或施工可行性论证。

planning-v24.json：各城方案和来源。validation-v24.json：v22 边界精确比对、13 条新线海陆和站位检查。render-validation-v24.json：云端浏览器检查；iPhone Safari 实机与 WebGL 设备未验证，不承诺零闪退或固定帧率。raster-memory-v24.json：影像像素与层级。

保留 v23 的玄武湖绕行、铁路统一符号、标签分级、历史地标来源、城市生活设施、岛内共享边界，以及西桥琥珀色/东桥蓝色。地标来源仍见 landmarks-research-v23.json；旧说明 README_v23.md。静态入口 static.html。

© OpenStreetMap contributors（ODbL）；Natural Earth 公共领域；台湾國土測繪中心开放道路资料；Mapzen Terrain Tiles。详见 planning-v24.json、corridors-v22.json。
''';(O/'README_v24.md').write_text(notes)
core=['index.html','atlas-mobile.html','manifest.webmanifest','icon-192.png','icon-512.png','static.html']+[p.name for p in sorted(O.glob('static-*-v24.svg'))]+[str(p.relative_to(O)) for p in sorted((O/'data').glob('v24*.js'))]
sw=(O/'sw.js').read_text();a=sw.index('CORE=')+5;b=sw.index(';',a);sw=sw[:a]+json.dumps(core,ensure_ascii=False)+sw[b:];sw=re.sub(r'moling-mobile-v\d+-r\d+-\d+','moling-mobile-v24-r1-20261027',sw);sw=re.sub(r"revision:'v\d+'","revision:'v24'",sw);sw=re.sub(r"rel.startsWith\('data/v\d+'\)","rel.startsWith('data/v24')",sw);sw=sw.replace('if(!r.ok||r.redirected)',"if(!r.ok||new URL(r.url).origin!==self.location.origin)");(O/'sw.js').write_text(sw)
extra=['sw.js','README_v21.md','README_v22.md','README_v23.md','README_v24.md','corridors-v22.json','island-bands-v22.json','validation-v22.json','render-validation-v22.json','revision-v20.json','ring-layout-v20.json','extension-v20.json','connectivity-v20.json','validation-v20.json','world-coordinates-v20.json','bohai-frontier-v20.json','planning-v24.json','validation-v24.json','render-validation-v24.json','raster-memory-v24.json','landmarks-research-v23.json'];extra=[n for n in extra if (O/n).is_file()]
def inline(m):return '<script>'+(O/m.group(1)).read_text().replace('</script','<\\/script')+'</script>'
single=re.sub(r'<script src="(data/v24[^\"]+\.js)"></script>',inline,s);assert '<script src="data/' not in single
public=core+extra+['final-html.json','final-zip.json']
def parts(kind,data):
 names=[]
 for i,start in enumerate(range(0,len(data),4*1024*1024),1):
  n=f'v24-{kind}-{i:02}.bin';(O/n).write_bytes(data[start:start+4*1024*1024]);names.append(n)
 (O/f'final-{kind}.json').write_text(json.dumps(dict(revision=REV,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),parts=names)));return names
public+=parts('html',gzip.compress(single.encode(),compresslevel=7,mtime=0));buf=io.BytesIO()
with ZipFile(buf,'w',ZIP_DEFLATED,compresslevel=7) as z:
 for n in core+extra:z.write(O/n,n)
public+=parts('zip',buf.getvalue());(T/'moling-atlas-v24.zip').write_bytes(buf.getvalue());public += [p.name for p in sorted(O.glob('广义建康-秣陵_*')) if p.suffix in ['.png','.svg']]+[p.name for p in sorted(O.glob('建康-丹阳_*')) if p.suffix in ['.png','.svg']];public=list(dict.fromkeys(public))
m=dict(revision=REV,source='https://moling-atlas-mobile.eliguli712.chatgpt.site',files=[dict(path=n,bytes=(O/n).stat().st_size,sha256=hashlib.sha256((O/n).read_bytes()).hexdigest()) for n in public]);(R/'asset-manifest-v24.json').write_text(json.dumps(m,ensure_ascii=False,indent=2));total=sum(a['bytes'] for a in m['files']);print('Packaged',len(public),'assets;',total,'bytes;ZIP',len(buf.getvalue()),flush=True)
p=R/'tools/generated-assets.json';gen=json.loads(p.read_text());gen['files']=[f for f in gen['files'] if not re.match(r'dist/(data/v(20|21|22|23|24)|v(20|21|22|23|24)-)',f['path'])];known={f['path'] for f in gen['files']}
for n in public:
 path='dist/'+n
 if path not in known and ((O/n).stat().st_size>1000000 or n in ['index.html','atlas-mobile.html','static.html']):gen['files'].append(dict(path=path))
p.write_text(json.dumps(gen,ensure_ascii=False,indent=2)+'\n');ignore=(R/'.gitignore').read_text().splitlines()+['/analysis-v24/','/tools/.*.??????']+['/'+f['path'] for f in gen['files']];(R/'.gitignore').write_text('\n'.join(dict.fromkeys(ignore))+'\n');assert total<267000000,total
