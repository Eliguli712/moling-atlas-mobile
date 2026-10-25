from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import json,gzip,re,hashlib,io
R=Path(__file__).resolve().parent.parent;O=R/'dist';deliver=R.parent/'deliverables';deliver.mkdir(exist_ok=True)
p=O/'index.html';s=p.read_text()
s=s.replace("link.dataset.fn=zip?'南齐世界地图_最终完整包.zip':'南齐世界地图_最终互动.html'", "link.download=zip?'南齐世界地图_v20.zip':'南齐世界地图_v20.html'")
# Site-relative aliases also work on GitHub project Pages and local extraction.
s=s.replace('https://moling-atlas-mobile.eliguli712.chatgpt.site','https://eliguli712.github.io/moling-atlas-mobile/')
p.write_text(s)
(O/'atlas-mobile.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>南齐世界地图 v20</title><a href="./index.html">打开地图</a><script>location.replace("./index.html"+location.search+location.hash)</script></html>')
core=['index.html','atlas-mobile.html','manifest.webmanifest','icon-192.png','icon-512.png']+[str(p.relative_to(O)) for p in sorted((O/'data').glob('v20*.js'))]
sw="""'use strict';
const CACHE='moling-mobile-v20-r3-20261025',CORE=__CORE__;
self.addEventListener('install',e=>e.waitUntil(self.skipWaiting()));
self.addEventListener('activate',e=>e.waitUntil((async()=>{for(const k of await caches.keys())if(k.startsWith('moling-mobile-')&&k!==CACHE)await caches.delete(k);await self.clients.claim()})()));
self.addEventListener('message',e=>{if(e.data?.type!=='CACHE_MAP')return;e.waitUntil((async()=>{try{const c=await caches.open(CACHE);for(const n of CORE){const u=new URL(n,self.registration.scope),r=await fetch(u,{cache:'reload'});if(!r.ok||r.redirected)throw Error('保存未完成');await c.put(u,r)}e.ports[0]?.postMessage({ok:true,revision:'v20'})}catch(err){e.ports[0]?.postMessage({ok:false,error:String(err)})}})())});
self.addEventListener('fetch',e=>{const u=new URL(e.request.url);if(u.origin!==location.origin||e.request.method!=='GET')return;const rel=u.pathname.slice(new URL(self.registration.scope).pathname.length);if(e.request.mode==='navigate'){e.respondWith((async()=>{try{const r=await fetch(e.request,{cache:'no-cache'});if(r.ok){const c=await caches.open(CACHE);await c.put(e.request,r.clone())}return r}catch(err){const c=await caches.open(CACHE);return await c.match(e.request)||await c.match(new URL('index.html',self.registration.scope))||Promise.reject(err)}})());return}if(!CORE.includes(rel))return;e.respondWith((async()=>{const c=await caches.open(CACHE);if(rel.startsWith('data/v20')){const cached=await c.match(e.request);if(cached)return cached}try{const r=await fetch(e.request);if(r.ok)await c.put(e.request,r.clone());return r}catch(err){return await c.match(e.request)||Promise.reject(err)}})())});
""".replace('__CORE__',json.dumps(core,ensure_ascii=False))
(O/'sw.js').write_text(sw)
notes='''# 南齐世界地图 v20

更新于 2026-10-25（渤海湾与东北接缝修订）。主站与镜像使用同一组带校验值的资料。

- 渤海湾按真实海岸接触段重分海域，移除契丹、库莫奚的误属海域；北魏东北外侧窄缝接入相邻部族的低强度活动带。北魏原始轮廓保持原样。
- 65 座城市、81 条环线按保留的地形、水系、城址和主干街道重新布局。车站保留身份，受影响的接轨线路共同重连。
- 北魏东北段恢复内嵌 v12 原始轮廓，补回营州的前 497 年郡县；东北名义区斜线面积为零。西部名义／实控图层保留。
- 默认希腊文标签，简化菜单首位提供球形切换；完整首帧显示，球面底图使用双线性采样。
- 新增 20 座城市、60 条地铁规划、20 条跨城与跨海走廊、29 座拜占庭机场。
- 日本八道：东海道、东山道、北陆道、山阴道、山阳道、南海道、西海道、北海道；畿内单列。此层采用后世区划作为地理参照。
- 海南、台湾共 13 个城域与部族分区；诸峒、诸社为沿海岸与河谷组织的架空自治规划。考古文化与现代族群身份分列。
- 琼州海峡东、西两条公铁桥；交州—广州滨海、晋兴—始安内陆、苍梧—湘江等走廊；沿线城轨设有共用节点的干线换乘。
- Αποκλειστική Οικονομική Ζώνη（ΑΟΖ）：200 海里经济海域示意，55 个沿海政权区域，和 12 海里领海独立开关。

## 直接定位

`#capital`、`#wei-ne`、`#japan`、`#jiaozhou`、`#islands`、`#byzantium`、`#aoz`；单城用 `#city=qv20_zhuyai` 等城市键。

## 资料与实现

城轨、机场、跨海桥、城域和经济海域属于本架空世界的规划资料。地形采用原包的现代 DEM 与水系参考。ΑΟΖ 外界采用 200 海里距离和球面近岸等距线概化。北魏州郡县仍是城址分区模型。

- 《魏书》卷106上： https://zh.wikisource.org/zh-hans/魏書/卷106上
- 海南省博物馆： https://www.hainanmuseum.org/hnbwgcms/info/597
- 台湾史前文化云： https://icloud.nmp.gov.tw/Classroom/Prehistoric?a=76
- 欧洲联盟《海洋法公约》希腊文： https://eur-lex.europa.eu/EL/legal-content/summary/united-nations-convention-on-the-law-of-the-sea.html

解压后打开 index.html。下载菜单中的单 HTML 版包含全部数据脚本。网站的“保存离线”会保存当前版本的 HTML 与配套数据。
'''
(O/'README_v20.md').write_text(notes)
# A separate complete single-file HTML is compressed and split for hosting.
def inline(m):
    code=(O/m.group(1)).read_text().replace('</script','<\\/script')
    return '<script>'+code+'</script>'
single=re.sub(r'<script src="(data/v20[^\"]+\.js)"></script>',inline,s)
payload=gzip.compress(single.encode(),compresslevel=7,mtime=0)
def parts(kind,b):
    names=[]
    for i,start in enumerate(range(0,len(b),4*1024*1024),1):
        n=f'v20-{kind}-{i:02}.bin';(O/n).write_bytes(b[start:start+4*1024*1024]);names.append(n)
    meta={'revision':'v20-r3','bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'parts':names}
    (O/f'final-{kind}.json').write_text(json.dumps(meta))
    return names
parts('html',payload)
buf=io.BytesIO()
with ZipFile(buf,'w',ZIP_DEFLATED,compresslevel=7) as z:
    for n in core+['sw.js','README_v20.md','revision-v20.json','ring-layout-v20.json','extension-v20.json','connectivity-v20.json','validation-v20.json','world-coordinates-v20.json','bohai-frontier-v20.json']:
        if (O/n).is_file():z.write(O/n,n)
zdata=buf.getvalue();parts('zip',zdata);(deliver/'moling-atlas-v20.zip').write_bytes(zdata)
# Only current files are needed to rebuild the public mirror. Older exports
# remain on the Site as labelled reference downloads.
public=core+['sw.js','README_v20.md','revision-v20.json','ring-layout-v20.json','extension-v20.json','connectivity-v20.json','validation-v20.json','world-coordinates-v20.json','bohai-frontier-v20.json','final-html.json','final-zip.json']
for kind in ['html','zip']:public+=json.loads((O/f'final-{kind}.json').read_text())['parts']
public=[n for n in public if (O/n).is_file()]
manifest={'revision':'v20-r3','source':'https://moling-atlas-mobile.eliguli712.chatgpt.site','files':[{'path':n,'bytes':(O/n).stat().st_size,'sha256':hashlib.sha256((O/n).read_bytes()).hexdigest()} for n in public]}
(R/'asset-manifest-v20.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print('Packaged',len(public),'public files; offline ZIP',len(zdata),'bytes; HTML gzip',len(payload),'bytes')
