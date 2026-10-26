"""Apply the v21 live rendering changes to the retained v20 HTML once."""
from pathlib import Path
import re
R=Path(__file__).resolve().parent.parent
p=R/'dist/index.html';s=p.read_text()
assert 'var HQ21=' not in s
s=s.replace('function PA(g){','function PA20(g){',1)
s=s.replace('ctx.stroke(pa)}})}','ctx.stroke(outline21(s.g))}})}',1)
s=s.replace('ctx.stroke(P_(z.g,true))','ctx.stroke(outline21(z.g))')
s=s.replace('ctx.stroke(P_(G.modern,true))','ctx.stroke(outline21(G.modern))')
s=s.replace("function drawSea19(){", "function drawSea19(){if(raster21Draw('sea'))return;")
s=s.replace("function drawHS(){", "function drawHS(){if(raster21Draw('shade'))return;")
s=s.replace('const sc=1.0,cap=FAST?1600:2200','const sc=1.0,cap=4096')
s=s.replace("const mx=VIEW==='plane'?BM:0","const mx=VIEW==='plane'?Math.min(BM,Math.max(0,(Math.sqrt(12000000/(W*H*dpr*dpr))-1)/2)):0")
# Adjacent Mercator raster strips share an integer device-pixel boundary.
s=s.replace("x0,y0,x1-x0,y1-y0+0.6)","x0,Math.round(y0*dpr)/dpr,x1-x0,(Math.round(y1*dpr)-Math.round(y0*dpr))/dpr)")
# Airport symbols enter only after regional zoom; names require a closer view.
s=s.replace("if(LY.airports20&&zl>.035)","if(LY.airports20&&zl>.65)")
s=s.replace(" if(LY.airports20){ctx.setTransform"," if(LY.airports20&&zoomLevel()>.35&&!(zoomLevel()>=.6&&LY.city2&&LY.xpr)){const occupied=[];ctx.setTransform")
s=s.replace("ctx.fillText('✈',p[0]-8,p[1]+5)","if(occupied.some(q=>Math.hypot(q[0]-p[0],q[1]-p[1])<35))continue;occupied.push(p);ctx.fillText('✈',p[0]-8,p[1]+5)")
s=s.replace("lw(bridge?5:road?3.6:3);","lw(bridge?5:road?3.6:l.role==='main'?4.4:l.role==='aux'?2.4:3.2);")
s=s.replace("lw(bridge?3:road?2.2:l.kind==='hsr'?1.9:1.4);","lw(bridge?3:road?2.2:l.role==='main'?2.7:l.role==='aux'?1.2:l.kind==='hsr'?1.9:1.8);")
s=s.replace("const b={xuanwu:","const b={liaodong:[[119.6,38.6],[126.3,42.6]],xuanwu:")

# Cache static extension geometry while keeping all symbols/text live.
a=s.index('function nDraw(){');b=s.index('\nfunction ',a+12)
fn=s[a:b];cut=fn.index(" ctx.setTransform(dpr,0,0,dpr,0,0);ctx.font=")
ground=fn[:cut].replace('function nDraw(){','function nDrawGround21(){')+' ctx.restore()}\n'
live="function nDraw(){if(!NX.data)return;ctx.save();"+fn[cut:]
s=s[:a]+ground+live+s[b:]
a=s.index('function extensionGround20(');b=s.index('\nfunction ',a+12);fn=s[a:b]
aa=fn.index(' if(LY.airports20');bb=fn.index('\n ctx.restore();',aa)
airport="function airportSymbols21(){const dark=isDark();ctx.save();"+fn[aa:bb]+"ctx.restore()}\n"
s=s[:a]+fn[:aa]+fn[bb:]+s[b:]
s=s.replace("  if(VIEW==='globe'){ctx.restore();ctx.strokeStyle=COL.rule;ctx.lineWidth=1;ctx.stroke(horizon())}","  nDrawGround21();extensionGround20(zl);\n  if(VIEW==='globe'){ctx.restore();ctx.strokeStyle=COL.rule;ctx.lineWidth=1;ctx.stroke(horizon())}",1)
s=s.replace('  nDraw();extensionGround20(zoomLevel());','')
s=s.replace('ctx.setTransform(dpr,0,0,dpr,0,0);drawPoints();labels();','ctx.setTransform(dpr,0,0,dpr,0,0);airportSymbols21();drawPoints();labels();nDraw();',1)
# Label collision queries use a spatial grid instead of scanning every label.
a=s.index('const put=',s.index('function labels(){'));b=s.index('\n  const zl=',a)
s=s[:a]+"const labelGrid21=new Map();const put=(x,y,txt,size,weight,col)=>worldLabel21(occ,DONE,labelGrid21,ff,x,y,txt,size,weight,col);"+s[b:]
# The named historical lake remains visible in the detailed world view.
s=s.replace('if(l.a<(zl>1?20:300))continue;','if(!l.focus&&l.a<(zl>1?20:300))continue;')
# Draw the historical water surface above surface streets, below live metro.
a=s.index('function drawCityGround(');b=s.index('\n}\nlet CITY_BASE',a)
s=s[:b]+"\n  if(J.xuanwu_v21){if(!J._xuanwu21)J._xuanwu21=pth([dloc(J.xuanwu_v21.r)],true);g.fillStyle=dk?'#1d4559':'#abd4e9';g.fill(J._xuanwu21);g.strokeStyle=dk?'#76b1cc':'#4d8eaf';L(.8);g.stroke(J._xuanwu21)}"+s[b:]
s=s.replace("if(!CM.lineFocus&&n.nf<2&&s<3&&ni%12!==0)","if(J.N.length>90&&!CM.lineFocus&&n.nf<2&&s<3&&ni%12!==0)")
s=s.replace("if(!CM.lineFocus&&n.nf<2&&s<6&&ni%4!==0)","if(J.N.length>90&&!CM.lineFocus&&n.nf<2&&s<6&&ni%4!==0)")
s=s.replace("const b={japan:","const b={liaodong:[[119.6,38.6],[126.3,42.6]],xuanwu:[[118.746,32.048],[118.851,32.114]],taiwan:[[119.9,21.7],[122.15,25.5]],japan:")
s=s.replace("for(let end=0;end<2;end++){const p=llToScr(...l.ends[end]);", "for(let end=0;end<(l.closed?1:2);end++){const p=llToScr(...l.ends[end]);")
s=s.replace("const nm=text20(l.n);", "const nm=LABEL20==='el'&&l.el?l.el:text20(l.n);")
s=s.replace("if(key==='capital')return;", "if(key==='capital'){closeCity();setView('plane');setProj('alb');HOMEP();openCity('q0000','network');return}")

s=s.replace('function nPrepCity(J){',"function nPrepCity(J){for(const n of [...J.N,...J.LRS])n.regionalTransfer=J.rsp.some(st=>Math.hypot(st.c[0]-n.c[0],st.c[1]-n.c[1])<.06);")
s=s.replace('if(n.nf>1){const rx=joint?', 'if(n.nf>1||n.regionalTransfer){const rx=joint?')
s=s.replace('const transfer=Number.isInteger(st.metro)||st.lightLines.length>1;', 'const transfer=Number.isInteger(st.metro)||st.lightLines.length>1||st.regionalTransfer;')
s=s.replace('if(rl||s>1.2)cLabelPut(g,occ,q[0],q[1],st.n,', 'if((rl||s>1.2)&&![...J.N,...J.LRS].some(n=>Math.hypot(n.c[0]-st.c[0],n.c[1]-st.c[1])<.06))cLabelPut(g,occ,q[0],q[1],st.n,')

# Explicit shortcuts for the new views in the existing compact toolbar.
s=s.replace("host.after(bar);apply();", "for(const [title,key] of [['玄武湖','xuanwu'],['台湾交通','taiwan'],['辽东铁路','liaodong']]){const b=document.createElement('button');b.className='btn';b.textContent=title;b.onclick=()=>goto20(key);host.append(b)}host.after(bar);apply();")
s=s.replace("document.documentElement.dataset.atlasReady='v20'","document.documentElement.dataset.atlasReady='v21'")
s=s.replace(" · v20`;"," · v21`;")
s=s.replace('<title>南齐世界地图 v20','<title>南齐世界地图 v21',1)
runtime=(R/'tools/render-v21.js').read_text().replace("$('cmap').dataset",'ccv.dataset')
s=s.replace('\ninitExtensions20();', '\n'+runtime+'\n'+airport+'\ninitExtensions20();',1)
p.write_text(s)
print('Patched live renderer and native-density viewport cache')
