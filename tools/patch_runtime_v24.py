"""Patch the retained v23-r2 runtime; exact baseline makes rebuilding idempotent."""
from atlas24_support import *
import re
s=generated_at('88b84d58a45fc128329f6a8c5cbda434c2c77968','dist/index.html').decode()
def replace(a,b):
 global s
 assert a in s,a[:100];s=s.replace(a,b)
s=s.replace('data/v23','data/v24').replace(' · v23',' · v24').replace('地图 v23','地图 v24').replace(' · v23</',' · v24</').replace(' · v23\'',' · v24\'').replace('v=23-r2','v=24-r1').replace('v=23-r1','v=24-r1').replace('README_v21.md','README_v24.md').replace('南齐世界地图_v21','南齐世界地图_v24')
# Remove a multi-megabyte hidden SVG tree from every interactive first load.
a=s.index('<section class="fb" id="fallback"');b=s.index('<main>',a);s=s[:a]+'<section class="fb" id="fallback" aria-label="静态版"><p>无需脚本的静态矢量图册：<a href="./static.html">打开静态地图与城市目录</a></p></section>\n'+s[b:]
s=s.replace('<details id="worldview23" open>','<details id="worldview23">')
replace('<script src="data/v24_d.js"></script>','<script src="data/v24_rasters.js"></script>\n<script src="data/v24_d.js"></script>')
# Serialized decompression limits transient encoded bytes and inflated JSON.
wrapper='''var NQ_DECODE24={active:0,peak:0,queue:[],limit:matchMedia('(max-width:900px),(pointer:coarse)').matches?1:2};
const decodeBase24=nqDecodeAsset;nqDecodeAsset=encoded=>new Promise((resolve,reject)=>{NQ_DECODE24.queue.push({encoded,resolve,reject});pumpDecode24()});
function pumpDecode24(){while(NQ_DECODE24.active<NQ_DECODE24.limit&&NQ_DECODE24.queue.length){const t=NQ_DECODE24.queue.shift();NQ_DECODE24.active++;NQ_DECODE24.peak=Math.max(NQ_DECODE24.peak,NQ_DECODE24.active);decodeBase24(t.encoded).then(t.resolve,t.reject).finally(()=>{NQ_DECODE24.active--;pumpDecode24()})}}
'''
replace('const NQ_ASSETS=Object.assign',wrapper+'const NQ_ASSETS=Object.assign')
replace('function openCity(k,tab,focusIndex){CM.pt.clear();','function openCity(k,tab,focusIndex){const req24=CM.request24=(CM.request24||0)+1;CM.pt.clear();')
replace('const done=J=>{if(CM.k!==k)return;','const done=J=>{if(CM.k!==k||CM.request24!==req24||$(\'cmodal\').hidden)return;')
replace('.then(j=>{const J=prepCity(j);CM.cache[k]=J;','.then(j=>{if(CM.k!==k||CM.request24!==req24||$(\'cmodal\').hidden||document.hidden)return;const J=prepCity(j);CM.cache[k]=J;')
replace(".catch(err=>{cmsg('城市数据未能加载", ".catch(err=>{if(CM.request24!==req24||CM.k!==k)return;cmsg('城市数据未能加载")
replace('ccv.width=Math.round(CM.W*CM.dpr);ccv.height=Math.round(CM.H*CM.dpr);creq()', 'const w24=Math.round(CM.W*CM.dpr),h24=Math.round(CM.H*CM.dpr);if(ccv.width!==w24)ccv.width=w24;if(ccv.height!==h24)ccv.height=h24;creq()')
replace("if(typeof CM!=='undefined'&&CM.cache[c.k]){consume(CM.cache[c.k]);return}nqFetch('c/'+c.k+'.json')", "if(typeof CM!=='undefined'&&CM.cache[c.k]){consume(CM.cache[c.k]);return Promise.resolve()}return nqFetch('c/'+c.k+'.json')")
replace('const consume=raw=>{const ll=xy=>', "const consume=raw=>{if(document.hidden||!$('cmodal').hidden||!detailCities24().has(c.k)){c._geographicPending=false;return}const ll=xy=>")
replace("promises.set(name,nqDecodeAsset(e).then(JSON.parse))}","promises.set(name,nqDecodeAsset(e).then(JSON.parse));const buses=[...promises.keys()].filter(k=>k.startsWith('bus/'));while(buses.length>2)promises.delete(buses.shift())}")
replace('HQ21.entries.length>4','HQ21.entries.length>(MOBILE24?1:3)')
replace('HQ21.pixels-=q.canvas.width*q.canvas.height}', 'HQ21.pixels-=q.canvas.width*q.canvas.height;q.canvas.width=q.canvas.height=1}')
replace('Math.min(1.4,Math.sqrt(12000000/(w0*h0*CM.dpr*CM.dpr)))','Math.max(1,Math.min(1.4,Math.sqrt((MOBILE24?4000000:8000000)/(w0*h0*CM.dpr*CM.dpr))))')
replace('  if(FAST)return;\n  const NU=', '  const NU=')
a=s.index(' // Predecode every retained raster');b=s.index(' Promise.allSettled(waits)',a);s=s[:a]+" const metas=activeRasters24().filter(Boolean);const waits=metas.map(m=>{hsImg(m);return HSI[m.f]?.ready24||Promise.resolve()});\n"+s[b:]
s=s.replace("dataset.atlasReady='v21'", "dataset.atlasReady='v24'")
# Shader objects can be released after successful link.
idx=s.index('class AtlasRaster21');a=s[:idx];tail=s[idx:];tail=tail.replace('gl.linkProgram(this.program);','gl.linkProgram(this.program);gl.deleteShader(vs);gl.deleteShader(fs);');s=a+tail
s=s.replace('龙城、扶余及辽东全境归高句丽，北魏直接接壤，两侧缓冲带渐隐显示','北魏东北边界与州郡县恢复保留的 v22 原始轮廓')
s=s.replace('initExtensions20();',(R/'tools/runtime-v24.js').read_text()+'\ninitExtensions20();')
(O/'index.html').write_text(s);print('Patched v24 runtime:',len(s),'characters')
