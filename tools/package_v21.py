"""Package one immutable v21 distribution for both public hosts."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import json,gzip,re,hashlib,io
R=Path(__file__).resolve().parent.parent;O=R/'dist';deliver=R.parent/'deliverables';deliver.mkdir(exist_ok=True)
p=O/'index.html';s=p.read_text();renames={}
for f in sorted((O/'data').glob('v20*.js')):
 n=re.sub(r'^v20(?:r\d+)?_', 'v21_',f.name);renames['data/'+f.name]='data/'+n;f.rename(f.with_name(n))
for old,new in renames.items():s=s.replace(old,new)
s=s.replace('南齐世界地图_v20.zip','南齐世界地图_v21.zip').replace('南齐世界地图_v20.html','南齐世界地图_v21.html')
s=s.replace('./南齐谷歌世界地图_互动.md','./README_v21.md')
s=s.replace('<a href="./nanqi-interactive-bundle.zip">网页与运行脚本 ZIP</a>','<button type="button" data-final-zip>v21 完整包 ZIP</button>')
p.write_text(s)
(O/'atlas-mobile.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>南齐世界地图 v21</title><a href="./index.html">打开地图</a><script>location.replace("./index.html"+location.search+location.hash)</script></html>')
core=['index.html','atlas-mobile.html','manifest.webmanifest','icon-192.png','icon-512.png','static.html']+[p.name for p in sorted(O.glob('static-*-v21.svg'))]+[str(p.relative_to(O)) for p in sorted((O/'data').glob('v21*.js'))]
old=(O/'sw.js').read_text();start=old.index('CORE=')+5;end=old.index(';',start)
old=old[:start]+json.dumps(core,ensure_ascii=False)+old[end:]
old=old.replace('moling-mobile-v20-r3-20261025','moling-mobile-v21-r1-20261026').replace("revision:'v20'","revision:'v21'").replace("rel.startsWith('data/v20')","rel.startsWith('data/v21')")
(O/'sw.js').write_text(old)
notes='''# 南齐世界地图 v21

2026-10-26 更新。主站和镜像共享同一份 SHA-256 校验清单。

- 宏观栅格按设备像素对齐，移除条带重叠接缝；跨经度接缝的面和轮廓分开生成，避免错误闭合产生水平、垂直长线。
- 平面底图按分辨率和视窗覆盖复用，最多四级、约 12 百万像素缓存。放大前重建足够清晰的底图；文字、站点、线路实时绘制，城市不再缩放旧的整帧截图。
- 支持 WebGL2 的设备使用 GPU 采样球面和区域高分辨率地形；其余设备使用 Canvas 回退。球面矢量按小于一个屏幕像素的误差简化，缓存分级几何；标签碰撞使用空间索引。
- 在线数据采用不可变 v21 地址与独立的服务工作线程缓存，刷新不混用旧版本数据；“保存离线”包含完整地图和所有城市。
- 建康补入玄武湖／后湖及名称，采用六朝水域的概化轮廓（模型约 15 km²），可由“玄武湖”快捷入口定位。古岸线未作精确测绘复原。
- 台湾保守方案：淡水津 1 条地铁、8 站；台江城 1 条地铁、9 站。大肚、兰阳、花莲、卑南各 1 条地面电车、6 站，站距约 1.05–1.2 km，无城市内部环线。
- 台湾环岛常规铁路与环岛公路闭合，经过六城干线换乘点。西岸为主干走廊，东岸和南段公路采用普通公路；苏花、南回铁路采用山麓、河谷和隧道廊道。交通仍属于本架空世界的规划。
- 辽东西岸纵贯主线约 436 km、东麓纵贯辅线约 478 km；和龙—辽东城货运联络线约 262 km，卑沙—鸭绿江—平壤货运干线约 472 km。路径按保留等高线的高程、坡度和陆地约束计算，非实测施工方案。
- 海南、台湾海岸采用 Natural Earth 1:1000万参考，分别 671 与 406 个轮廓点；内部 6／7 个活动区沿山脉、河谷的通行代价划分，保持共享边界和完整陆地覆盖。
- 新增无脚本静态矢量图册：五幅同步地图和全部 262 城交通表；移除旧版静态图片与过期统计。拜占庭机场在区域放大后再显示，宏观视图不显示。
- 北魏原始边界、东北部族接缝、渤海湾海域归属及希腊文默认设置延续上一版。验证报告保留这些数据的 SHA-256 摘要。

## 定位

`#xuanwu`、`#taiwan`、`#liaodong`、`#wei-ne`、`#japan`、`#jiaozhou`、`#islands`、`#byzantium`、`#aoz`；单城用 `#city=qv20_danshui` 等城市键。

## 玄武湖参考

- 玄武湖景区官方简介（名称起源、六朝用途）：https://www.xuanwuhu.net/mhls/mhls1.aspx
- 景区历史资料：https://www.xuanwuhu.net/mhls/detail.aspx?id=242

解压后打开 index.html；单 HTML 下载内嵌全部数据。性能记录说明测试环境与采样口径，不承诺所有设备达到固定帧率。
'''
(O/'README_v21.md').write_text(notes)
extra=['sw.js','README_v21.md','validation-v21.json','render-validation-v21.json','revision-v20.json','ring-layout-v20.json','extension-v20.json','connectivity-v20.json','validation-v20.json','world-coordinates-v20.json','bohai-frontier-v20.json']
extra=[n for n in extra if (O/n).is_file()]
def inline(m):return '<script>'+(O/m.group(1)).read_text().replace('</script','<\\/script')+'</script>'
single=re.sub(r'<script src="(data/v21[^\"]+\.js)"></script>',inline,s)
assert '<script src="data/' not in single
for f in O.glob('v20-*.bin'):f.unlink()
def parts(kind,data):
 names=[]
 for i,start in enumerate(range(0,len(data),4*1024*1024),1):
  n=f'v21-{kind}-{i:02}.bin';(O/n).write_bytes(data[start:start+4*1024*1024]);names.append(n)
 meta=dict(revision='v21-r1',bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),parts=names);(O/f'final-{kind}.json').write_text(json.dumps(meta));return names
public=core+extra+['final-html.json','final-zip.json']
public+=parts('html',gzip.compress(single.encode(),compresslevel=7,mtime=0))
buf=io.BytesIO()
with ZipFile(buf,'w',ZIP_DEFLATED,compresslevel=7) as z:
 for n in core+extra:z.write(O/n,n)
public+=parts('zip',buf.getvalue());(deliver/'moling-atlas-v21.zip').write_bytes(buf.getvalue())
public+=[p.name for p in sorted(O.glob('广义建康-秣陵_*')) if p.suffix in ['.svg','.png']]
public+=[p.name for p in sorted(O.glob('建康-丹阳_*')) if p.suffix in ['.svg','.png']]
public=list(dict.fromkeys(public))
manifest={'revision':'v21-r1','source':'https://moling-atlas-mobile.eliguli712.chatgpt.site','files':[dict(path=n,bytes=(O/n).stat().st_size,sha256=hashlib.sha256((O/n).read_bytes()).hexdigest()) for n in public]}
(R/'asset-manifest-v21.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
# Retain older source assets, replace only the generated current distribution.
p=R/'tools/generated-assets.json';m=json.loads(p.read_text());m['files']=[f for f in m['files'] if not f['path'].startswith(('dist/data/v20','dist/v20-'))]
known={f['path'] for f in m['files']}
for n in public:
 path='dist/'+n
 if path not in known and ((O/n).stat().st_size>1000000 or n in ['index.html','atlas-mobile.html']):m['files'].append({'path':path})
p.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
with (R/'.gitignore').open('a') as f:
 for n in public:
  if any(v['path']=='dist/'+n for v in m['files']):f.write('\n/dist/'+n)
print('Packaged',len(public),'verified v21 assets; ZIP',len(buf.getvalue()),'bytes')
