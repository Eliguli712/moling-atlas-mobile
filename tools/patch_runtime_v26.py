"""Keep v25 rendering improvements; repair frontier policy and cache identity."""
from atlas26_support import R,O,BASE,generated_at
s=generated_at(BASE,'dist/index.html').decode()
s=s.replace('data/v25','data/v26').replace(' · v25',' · v26').replace('地图 v25','地图 v26').replace('v=25-r1','v=26-r1').replace('README_v25.md','README_v26.md').replace('南齐世界地图_v25','南齐世界地图_v26')
s=s.replace('两方主张可重叠。','所有强度层均排除北魏领土。').replace('高句丽实色为实际控制，外围淡色为较弱影响','高句丽使用多层地形控制场，外围淡色为较弱影响').replace('双方接壤缓冲区','高句丽一侧缓冲区')
a="if(sel.type==='p5'&&P5[sel.id].nm!==1&&P5[sel.id].frontier_outline_stroke!==false)hl(P5[sel.id].g,COL.focus,2.4);"
b="if(sel.type==='p5'&&P5[sel.id].nm!==1&&P5[sel.id].frontier_outline_stroke!==false){const s26=P5[sel.id];if(s26.en==='Koguryo'&&D.v26)selectedGog26(s26.g,COL.focus,2.4,hl);else hl(s26.g,COL.focus,2.4);}"
assert a in s;s=s.replace(a,b)
s=s.replace("dataset.atlasReady='v25'", "dataset.atlasReady='v26'")
assert 'initExtensions20();' in s;s=s.replace('initExtensions20();',(R/'tools/runtime-v26.js').read_text()+'\ninitExtensions20();')
(O/'index.html').write_text(s);print('Patched v26 runtime; exclusive fills and selection; fresh data URLs')
