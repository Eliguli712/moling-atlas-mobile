"""Ordinary railway ties and geographic corridor credits; retain v21 renderer."""
from pathlib import Path
R=Path(__file__).resolve().parents[1];p=R/'dist/index.html';s=p.read_text()
s=s.replace('data/v21_d.js','data/v22_d.js').replace('sw.js?v=20-r3','sw.js?v=22-r1').replace('南齐世界地图 v21','南齐世界地图 v22').replace('· v21','· v22')
a=s.index(' if(LY.transport20)for(const l of E20.routes)');b=s.index('\n\n ctx.restore();',a)
s=s[:a]+''' if(LY.transport20)for(const l of E20.routes){
  if(!inView(l.g))continue;
  const road=l.kind==='road',bridge=l.kind==='bridge',rail=l.kind==='rail'||l.kind==='regional',aux=l.role==='aux',path=P_(l.g,false);
  const dash=v=>ctx.setLineDash(VIEW==='plane'?v.map(x=>x/view.s):v);
  ctx.lineCap='round';ctx.lineJoin='round';ctx.setLineDash([]);
  ctx.strokeStyle=dark?'#202d2b':'#fffdf5';lw(bridge?5:road?3.6:rail?(aux?5:6.7):4);ctx.stroke(path);
  if(rail){
   ctx.strokeStyle=dark?'#c9d2cc':'#424941';ctx.lineCap='butt';
   if(zl>.035){lw(aux?4.3:5.5);dash([1.1,7]);ctx.stroke(path);ctx.setLineDash([])}
   lw(aux?1.1:1.6);ctx.stroke(path);
  }else{
   ctx.strokeStyle=bridge?'#14797e':road?'#b98332':'#ac325e';lw(bridge?3:road?2.2:1.9);
   if(!road&&!bridge)dash([7,2]);ctx.stroke(path);ctx.setLineDash([]);
  }
 }
''' +s[b:]
s=s.replace("l.kind==='road'?'#926225':'#71446f'","l.kind==='road'?'#926225':l.kind==='hsr'?'#71446f':'#424941'")
credit='<p class="note">交通廊道参考：<a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">© OpenStreetMap contributors · ODbL</a>、Natural Earth、<a href="https://data.gov.tw/dataset/73232" target="_blank" rel="noopener">國土測繪中心道路图资</a>。现代线路仅作为497架空规划的地形参考；城郊站沿连续路网接轨。</p>'
if credit not in s:s=s.replace("$('tree').prepend(panel);", "panel.insertAdjacentHTML('beforeend',"+repr(credit)+");$('tree').prepend(panel);")
css='<style id="static-v22-layout">#fallback svg{display:block;width:100%;height:auto}#fallback figure{margin:16px 0}</style>'
if css not in s:s=s.replace('</head>',css+'</head>')
p.write_text(s)
print('Ordinary railway symbols and corridor credits applied')
