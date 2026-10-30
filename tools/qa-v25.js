var QA25=document.createElement('div');QA25.id='qa25';QA25.style='position:fixed;bottom:0;left:0;background:#fff;z-index:99999;font:11px sans-serif;padding:4px;max-width:100vw';document.body.append(QA25);
function qa25(name,fn){const b=document.createElement('button');b.textContent=name;b.onclick=fn;QA25.append(b)}
qa25('辽东',()=>{closeCity();setView('globe');GP='ortho';gv={lon:123,lat:41.8,k:16};draw();legend()});
qa25('玄武湖高倍',()=>{closeCity();setView('globe');GP='ortho';gv={lon:118.795,lat:32.086,k:3000};draw();legend()});
qa25('透视边缘',()=>{closeCity();setView('globe');GP='persp';ALT=3000;TILT=65;gv={lon:121,lat:39.5,k:18};draw();legend()});
qa25('CPU回退',()=>{if(RG21&&RG21!==false)RG21.gl.getExtension('WEBGL_lose_context')?.loseContext();RG21=false;BDIRTY=true;draw()});
qa25('百倍',()=>{closeCity();setView('globe');GP='ortho';gv={lon:118.795,lat:32.086,k:100};draw()});
qa25('晋安',()=>openCity('q0065','network'));qa25('建康',()=>openCity('q0000','network'));qa25('淡水',()=>openCity('qv20_danshui','network'));qa25('关闭城市',()=>closeCity());
qa25('收起测量',()=>{$('qa25output')?.remove();$('qa25timings')?.remove()});
qa25('测量',()=>{const b=$('map').dataset,rect=WORLD_LABELS||[];let overlap=0;for(let i=0;i<rect.length;i++)for(let j=0;j<i;j++)if(!(rect[i][2]<rect[j][0]||rect[j][2]<rect[i][0]||rect[i][3]<rect[j][1]||rect[j][3]<rect[i][1]))overlap++;let o=$('qa25output');if(!o){o=document.createElement('pre');o.id='qa25output';QA25.append(o)}o.textContent=JSON.stringify({release:document.body.dataset.atlasRelease,view:VIEW,projection:GP,k:gv.k,dpr,geometryBytes:GEOM23.bytes,geometryBudget:GEOM23.limit,meshTriangles:b.meshTriangles,meshSamples:b.meshSamples,meshPixels:b.meshPixels,rasterPixels:b.decodedRasterPixels,labelCount:rect.length,labelOverlap:overlap,city:CM.k,cityLoaded:!!CM.J,decodeActive:NQ_DECODE24.active,decodeQueued:NQ_DECODE24.queue.length},null,1)});
qa25('平移计时',()=>{const times=[];for(let i=0;i<6;i++){gv.lon+=.015;BDIRTY=true;const start=performance.now();drawNow();times.push(Math.round(performance.now()-start))}const p=document.createElement('pre');p.id='qa25timings';p.textContent=JSON.stringify(times);QA25.append(p)});

