"""Package one immutable v22 distribution for both public hosts."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import json,gzip,re,hashlib,io
R=Path(__file__).resolve().parent.parent;O=R/'dist';deliver=R.parent/'deliverables';deliver.mkdir(exist_ok=True)
p=O/'index.html';s=p.read_text().replace('v21 完整包','v22 完整包').replace('README_v21.md','README_v22.md').replace('南齐世界地图_v21','南齐世界地图_v22')
p.write_text(s)
for f in list(O.glob('v21-*.bin'))+list(O.glob('v22-*.bin'))+list(O.glob('static-*-v21.svg'))+[O/'data/v21_d.js']:
 if f.exists():f.unlink()
(O/'atlas-mobile.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>南齐世界地图 v22</title><a href="./index.html">打开地图</a><script>location.replace("./index.html"+location.search+location.hash)</script></html>')
core=['index.html','atlas-mobile.html','manifest.webmanifest','icon-192.png','icon-512.png','static.html']+[p.name for p in sorted(O.glob('static-*-v22.svg'))]+[str(p.relative_to(O)) for p in sorted(list((O/'data').glob('v21*.js'))+list((O/'data').glob('v22*.js')))]
old=(O/'sw.js').read_text();start=old.index('CORE=')+5;end=old.index(';',start)
old=old[:start]+json.dumps(core,ensure_ascii=False)+old[end:]
old=old.replace('moling-mobile-v21-r1-20261026','moling-mobile-v22-r1-20261026').replace("revision:'v21'","revision:'v22'").replace("if(rel.startsWith('data/v21'))","if(rel.startsWith('data/v21')||rel.startsWith('data/v22'))").replace("revision:'v20'","revision:'v22'").replace("rel.startsWith('data/v20')","rel.startsWith('data/v22')")
(O/'sw.js').write_text(old)
notes='''# 南齐世界地图 v22

2026-10-26 更新。两站使用同一份 SHA-256 校验清单。

- 重建交广、海岛、辽东及罗马的 22 条陆上交通廊道，保留详细地形转折和连续接轨关系。删除新增干线中少量控制点造成的长距离城际直连；不以周期摆动或单纯加密点模拟地形。
- 辽东西岸主线、东麓辅线和两条跨国货运线，使用铁路参考廊道布线；岫岩另设约81公里山地支线。普通铁路显示深灰轨道与枕木，辅线线宽略小；跨河沿桥位通过，山区沿现有桥隧廊道参考。
- 海南与台湾环线沿连续沿岸、河谷通道闭合；台湾诸社活动区清除横向扫描条带，保持原海岸和完整覆盖。普通公路、铁路与高速铁路仍使用各自符号。
- 城郊接轨站放在线路上，保留原城址供对照；不强制把城中心直接连到轨道。
- 同步更新无脚本静态图册、单 HTML 和完整 ZIP，独立 v22 缓存配合不变的 v21 城市资料。
- 沿用 v21 的实时清晰底图、分辨率缓存、玄武湖、台湾保守城市地铁方案、希腊文默认名称、紧凑球形按钮和机场分级显示。北魏疆界、渤海湾海域及东北部族衔接数据保留原校验摘要。

## 资料与使用范围

这些是 **497 架空世界交通规划**。OpenStreetMap 的现代铁路／公路和 Natural Earth 参考用于选择真实地形中的通行廊道；不表示相应工程在497年存在，也不作为实测工程设计。新增规划铁路在缺少连续铁路资料的区域，采用公路通行廊道作地理参考。跨琼州海峡两座桥仍为架空规划。

© OpenStreetMap contributors，依据 ODbL 1.0 使用。台湾公路使用國土測繪中心官方道路中线，依据政府資料開放授權條款第1版使用。参考路线及来源随源码 tools/corridors-v22.geojson 一并提供。

- https://www.openstreetmap.org/copyright
- https://wiki.openstreetmap.org/wiki/Overpass_API
- https://data.gov.tw/dataset/73232 （台湾道路：內政部國土測繪中心，政府資料開放授權條款第1版）
- https://www.naturalearthdata.com/ （公共领域，1:1000万概化参考）
- https://www.igsnrr.cas.cn/cbkx/kpyd/zgdl/cnh/202009/t20200910_5692432.html （辽东山脉与水系）

## 定位与检查

`#liaodong`、`#jiaozhou`、`#islands`、`#taiwan`、`#xuanwu`。static.html 可无脚本打开。

详细线路点数、里程、接轨站偏移及资料来源见 corridors-v22.json；原有保护数据摘要见 validation-v22.json。更多前期修订见 README_v21.md。
'''
(O/'README_v22.md').write_text(notes)
extra=['sw.js','README_v21.md','corridors-v22.json','island-bands-v22.json','README_v22.md','validation-v22.json','render-validation-v22.json','revision-v20.json','ring-layout-v20.json','extension-v20.json','connectivity-v20.json','validation-v20.json','world-coordinates-v20.json','bohai-frontier-v20.json']
extra=[n for n in extra if (O/n).is_file()]
def inline(m):return '<script>'+(O/m.group(1)).read_text().replace('</script','<\\/script')+'</script>'
single=re.sub(r'<script src="(data/v(?:21|22)[^\"]+\.js)"></script>',inline,s)
assert '<script src="data/' not in single
for f in O.glob('v20-*.bin'):f.unlink()
def parts(kind,data):
 names=[]
 for i,start in enumerate(range(0,len(data),4*1024*1024),1):
  n=f'v22-{kind}-{i:02}.bin';(O/n).write_bytes(data[start:start+4*1024*1024]);names.append(n)
 meta=dict(revision='v22-r1',bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),parts=names);(O/f'final-{kind}.json').write_text(json.dumps(meta));return names
public=core+extra+['final-html.json','final-zip.json']
public+=parts('html',gzip.compress(single.encode(),compresslevel=7,mtime=0))
buf=io.BytesIO()
with ZipFile(buf,'w',ZIP_DEFLATED,compresslevel=7) as z:
 for n in core+extra:z.write(O/n,n)
public+=parts('zip',buf.getvalue());(deliver/'moling-atlas-v22.zip').write_bytes(buf.getvalue())
public+=[p.name for p in sorted(O.glob('广义建康-秣陵_*')) if p.suffix in ['.svg','.png']]
public+=[p.name for p in sorted(O.glob('建康-丹阳_*')) if p.suffix in ['.svg','.png']]
public=list(dict.fromkeys(public))
manifest={'revision':'v22-r1','source':'https://moling-atlas-mobile.eliguli712.chatgpt.site','files':[dict(path=n,bytes=(O/n).stat().st_size,sha256=hashlib.sha256((O/n).read_bytes()).hexdigest()) for n in public]}
(R/'asset-manifest-v22.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
# Retain older source assets, replace only the generated current distribution.
p=R/'tools/generated-assets.json';m=json.loads(p.read_text());m['files']=[f for f in m['files'] if not f['path'].startswith(('dist/data/v20','dist/v20-','dist/v21-','dist/v22-','dist/data/v21_d.js'))]
known={f['path'] for f in m['files']}
for n in public:
 path='dist/'+n
 if path not in known and ((O/n).stat().st_size>1000000 or n in ['index.html','atlas-mobile.html']):m['files'].append({'path':path})
p.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
with (R/'.gitignore').open('a') as f:
 for n in public:
  if any(v['path']=='dist/'+n for v in m['files']):f.write('\n/dist/'+n)
print('Packaged',len(public),'verified v22 assets; ZIP',len(buf.getvalue()),'bytes')
