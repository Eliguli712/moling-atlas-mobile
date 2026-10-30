"""Idempotently patch the immutable published v24 source."""
from atlas24_support import generated_at,R,O
import re
s=generated_at('cc14b1ddbb303058cd706605494981432aa18ea3','dist/index.html').decode()
def rep(a,b):
 global s
 assert a in s,a[:150]
 s=s.replace(a,b)
s=s.replace('data/v24','data/v25').replace(' · v24',' · v25').replace('地图 v24','地图 v25').replace('v=24-r1','v=25-r1').replace('README_v24.md','README_v25.md').replace('南齐世界地图_v24','南齐世界地图_v25')
rep("for(const s of STS){if(LY.am18&&s.en==='Maya states')continue;", "for(const s of STS){if(s.en==='Koguryo'&&D.v25){drawGogField25(s,zl);continue}if(LY.am18&&s.en==='Maya states')continue;")
rep("if(LY.nomad&&!LY.season){const __wn=WNOM();", "if(LY.nomad&&!LY.season){ctx.save();const fg25=frontier25()?.control;if(fg25){const cp25=new Path2D();cp25.rect(-1e8,-1e8,2e8,2e8);cp25.addPath(P_(fg25,true));ctx.clip(cp25,'evenodd')}const __wn=WNOM();")
rep("ctx.globalAlpha=1}if(__wn)ctx.restore()}", "ctx.globalAlpha=1}if(__wn)ctx.restore();ctx.restore()}")
rep('macroNames20(put,zl);extensionLabels20(put,zl);','macroNames20(put,zl);')
rep('\n}\nfunction scale(){','\n extensionLabels20(put,zl);\n}\nfunction scale(){')
rep("(isDark()?'#a8a39a':'#6d6a63')", "(isDark()?'#a8a39a':'#8d8a83')")
rep('lw(bridge?3:road?2.2:hs?3:aux?1.5:2.2);','lw(bridge?3:road?2.2:hs?3:zl>.4?1.1:.7);')
rep('if(!road&&!bridge){ctx.strokeStyle=COL.panel;', 'if(hs){ctx.strokeStyle=COL.panel;')
rep("const decodeBase24=nqDecodeAsset;nqDecodeAsset=encoded=>new Promise((resolve,reject)=>{NQ_DECODE24.queue.push({encoded,resolve,reject});pumpDecode24()});", "var NQ_CONTEXT25=()=>null,NQ_STALE25=()=>false;const decodeBase24=nqDecodeAsset;nqDecodeAsset=(encoded,name)=>new Promise((resolve,reject)=>{NQ_DECODE24.queue.push({encoded,resolve,reject,name,context:NQ_CONTEXT25(name)});pumpDecode24()});")
rep('function pumpDecode24(){while(', "document.addEventListener('visibilitychange',()=>{if(!document.hidden)pumpDecode24()});\nfunction pumpDecode24(){if(document.hidden)return;while(")
rep('const t=NQ_DECODE24.queue.shift();NQ_DECODE24.active++;', "const t=NQ_DECODE24.queue.shift();if(NQ_STALE25(t)){const e=new Error('视图已更新');e.name='AbortError';t.reject(e);continue}NQ_DECODE24.active++;")
rep('await nqDecodeAsset(encoded)', 'await nqDecodeAsset(encoded,name)')
rep('nqDecodeAsset(e).then(JSON.parse)', 'nqDecodeAsset(e,name).then(JSON.parse)')
# A fresh request must never reuse a queued promise from an obsolete city epoch.
# An obsolete promise's finally handler must not delete its replacement.
rep('if(!RAW_CITY24.pending.has(name)){', 'const previous25=RAW_CITY24.pending.get(name);if(previous25&&previous25.epoch24!==RAW_CITY24.epoch)RAW_CITY24.pending.delete(name);if(!RAW_CITY24.pending.has(name)){')
rep('.finally(()=>RAW_CITY24.pending.delete(name));RAW_CITY24.pending.set(name,p)', '.finally(()=>{if(RAW_CITY24.pending.get(name)===p)RAW_CITY24.pending.delete(name)});p.epoch24=epoch;RAW_CITY24.pending.set(name,p)')
rep("for(const a of J._poi23||[]){if(tab!=='life23'", "for(const a of J._poi23||[]){if(!poiVisible25(a))continue;if(tab!=='life23'")
rep('initExtensions20();',(R/'tools/runtime-v25.js').read_text()+'\ninitExtensions20();')
s=s.replace("dataset.atlasReady='v24'", "dataset.atlasReady='v25'")
(O/'index.html').write_text(s);print('Patched v25 runtime',len(s),'characters')
