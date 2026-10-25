from pathlib import Path
import re,json
R=Path(__file__).resolve().parent.parent;p=R/'dist/index.html';s=p.read_text()
def sub(a,b):
    global s
    if a not in s:raise ValueError('Missing patch marker '+a[:100])
    s=s.replace(a,b)
sub('<title>南齐世界地图 v19</title>','<title>南齐世界地图 v20 · 山海与诸国</title>')
sub('<script src="data/v20_a4_0.js">','<script src="data/v20_extra.js"></script>\n<script src="data/v20_a4_0.js">')
sub('const NQ_ASSETS=Object.assign({},globalThis.__NQA4_0','const NQ_ASSETS=Object.assign({},globalThis.__NQA20,globalThis.__NQA4_0')
# This code lives in the atlas closure, sharing source geometry and picking.
sub("nInit();cityHistoryInit();finalInit();",(R/'tools/v20-runtime.js').read_text()+"\nnInit();cityHistoryInit();finalInit();")
sub("document.documentElement.classList.add('ready','js');","initExtensions20();\ndocument.documentElement.classList.add('ready','js');")
sub('function drawNow(){if(!W)return;','function drawNow(){if(!W||!READY20)return;')
sub('function resize(){const r=wrap.getBoundingClientRect();dpr=nqDpr(r.width,r.height);W=r.width;H=r.height;cv.width=Math.round(W*dpr);cv.height=Math.round(H*dpr);draw()}',
    'function resize(){const r=wrap.getBoundingClientRect(),nd=nqDpr(r.width,r.height),nw=Math.round(r.width*nd),nh=Math.round(r.height*nd);dpr=nd;W=r.width;H=r.height;if(cv.width!==nw||cv.height!==nh){cv.width=nw;cv.height=nh;BV=null}draw()}')
sub("ctx0.imageSmoothingEnabled=true;", "ctx0.imageSmoothingEnabled=true;ctx0.imageSmoothingQuality='high';")
sub("ctx.imageSmoothingEnabled=true;", "ctx.imageSmoothingEnabled=true;ctx.imageSmoothingQuality='high';")
sub('Math.abs(Math.log(view.s/SV.s))<2.5','Math.abs(Math.log(view.s/SV.s))<.24')
sub("if(FAST&&BV&&VIEW==='plane'&&BV.v==='plane'&&BV.p===PROJ&&BV.W===W&&BV.H===H){compose(true);", "if(FAST&&BV&&VIEW==='plane'&&BV.v==='plane'&&BV.p===PROJ&&BV.W===W&&BV.H===H){if(Math.abs(Math.log(view.s/BV.s))>.24){const f=FAST;FAST=false;renderBase(key);FAST=f}compose(true);")
sub('const NU=48,NV=Math.max(12,Math.round(48*m.H/m.W))','const NU=Math.max(96,Math.min(240,Math.ceil(W/8))),NV=Math.max(24,Math.round(NU*m.H/m.W))')
sub("const NS=48,x0=", "const NS=Math.max(96,Math.min(512,Math.ceil(H/6))),x0=")
sub("TW=small?2048:4096", "TW=4096")
sub('const sc=FAST?0.55:1.0,cap=FAST?560:1400;', 'const sc=1.0,cap=FAST?1600:2200;')
# Bilinear globe sampling removes the nearest-neighbour block pattern.
old="let u=((d+lon0)*ku)|0;u%=TW;if(u<0)u+=TW;let v=((90-L[2*q+1])*kv)|0;if(v<0)v=0;else if(v>=TH)v=TH-1;const t=v*TW+u;oS[q]=T.sea[t];oH[q]=T.sh[t]"
new="let fu=(d+lon0)*ku-.5;fu=((fu%TW)+TW)%TW;let fv=Math.max(0,Math.min(TH-1,(90-L[2*q+1])*kv-.5));const u=fu|0,v=fv|0,u1=(u+1)%TW,v1=Math.min(TH-1,v+1),a=fu-u,b=fv-v,t=v*TW+u,t1=v*TW+u1,t2=v1*TW+u,t3=v1*TW+u1;const blend=(S)=>{const A=S[t],B=S[t1],C=S[t2],E=S[t3];let o=0;for(let k=0;k<24;k+=8){const x=((A>>>k)&255)*(1-a)*(1-b)+((B>>>k)&255)*a*(1-b)+((C>>>k)&255)*(1-a)*b+((E>>>k)&255)*a*b;o|=Math.round(x)<<k}return (o|0xff000000)>>>0};oS[q]=blend(T.sea);oH[q]=blend(T.sh)"
sub(old,new)
sub('  drawDist();','  extensionGround20(zl);drawDist();')
sub('function labels(){const occ=[];','function labels(){const occ=[];')
sub('put=(x,y,txt,size,weight,col)=>{if(DONE.has(txt)', 'put=(x,y,txt,size,weight,col)=>{txt=text20(txt);if(DONE.has(txt)')
sub('  const zl=zoomLevel();\n  if((LY.city2||LY.metro)', '  const zl=zoomLevel();macroNames20(put,zl);extensionLabels20(put,zl);\n  if((LY.city2||LY.metro)')
sub('p.zh,zl>0.15?12:10.5','name20(p),zl>0.15?12:10.5')
sub("c.n+(zl>0.8?' '+c.zh:'')", "name20(c)+(zl>0.8&&LABEL20==='el'?' '+c.zh:'')")
sub("zl>0.5?c.lat_name+' '+nm:nm", "LABEL20==='el'?c.el:(zl>0.5?c.lat_name+' '+nm:nm)")
sub('function cityDisplay(c){return c.historical_name?.display||c.n}', "function cityDisplay(c){return LABEL20==='el'&&c.el?c.el:(c.historical_name?.display||c.n)}")
sub('${s.zh}<em>${s.en}</em>', '${s.zh}<em>${name20(s)}</em>')
sub('card(s.zh,s.en+', 'card(s.zh,name20(s)+')
sub('li(s.zh,s.en,', 'li(s.zh,name20(s),')
sub("if(s.zh.includes(q)||s.en.toLowerCase().includes(q.toLowerCase()))", "if(s.zh.includes(q)||(s.el||'').toLowerCase().includes(q.toLowerCase())||s.en.toLowerCase().includes(q.toLowerCase()))")
sub(" · v19`;", " · v20`;")
# The viewport strip is scrollable at every narrow width, and buttons never
# collapse into one-character vertical labels as in the supplied screenshot.
sub('@media (max-width:700px){#views18{flex-wrap:nowrap;', '@media (max-width:760px){#views18{flex-wrap:nowrap;')
sub("const KEY='nq-atlas-simple';let simple=true;try{const v=localStorage.getItem(KEY);if(v==='0')simple=false}catch(e){}", "const KEY='nq-atlas-simple-v20';let simple=true;")
# Registered workers use one atomic revision for navigation and script chunks.
sub("navigator.serviceWorker.register('./sw.js')", "navigator.serviceWorker.register('./sw.js?v=20',{updateViaCache:'none'})")
s=s.replace(' · 地球',' · 球形').replace('地球视图','球形视图')
p.write_text(s)
print('Patched v20 runtime',p.stat().st_size)

# Compute node positions before joint-view labels at every zoom.
s=p.read_text().replace("J.N.filter(n=>vis(n.gq))","J.N.filter(n=>{n.gq=toS(n.c);return vis(n.gq)})");p.write_text(s)
