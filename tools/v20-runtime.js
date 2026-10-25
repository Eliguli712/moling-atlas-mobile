/* v20: shared display, island planning and named transport layers. */
const EXT20=D.v20_ext||{routes:[],airports:[],islands:[],japan:[]};
let LABEL20='el',READY20=false;
const L20LOOK=new Map((D.p500||[]).map(s=>[s.en,s.el||s.zh]));
for(const c of [...D.bz17?.city||[],...D.eu18?.city||[]]){if(c.en)L20LOOK.set(c.en,c.el||c.n);if(c.lat_name)L20LOOK.set(c.lat_name,c.el||c.zh)}
function name20(o){return LABEL20==='el'?(o.el||o.n||o.zh):LABEL20==='en'?(o.en||o.lat_name||o.n||o.zh):(o.zh||o.n)}
function greekText20(s){const pairs={th:'θ',ph:'φ',ch:'χ',sh:'σ',kh:'χ',oo:'ου',ou:'ου',ai:'αι',ei:'ει',ng:'νγκ',ts:'τσ'},abc={a:'α',b:'β',c:'κ',d:'δ',e:'ε',f:'φ',g:'γ',h:'χ',i:'ι',j:'τζ',k:'κ',l:'λ',m:'μ',n:'ν',o:'ο',p:'π',q:'κ',r:'ρ',s:'σ',t:'τ',u:'ου',v:'β',w:'ου',x:'ξ',y:'υ',z:'ζ'};let out='';for(let i=0;i<s.length;){const d=s.slice(i,i+2).toLowerCase(),found=pairs[d],v=found||abc[s[i].toLowerCase()]||s[i];out+=s[i]===s[i].toUpperCase()?v[0].toUpperCase()+v.slice(1):v;i+=found?2:1}return out.replace(/σ(?=\s|$)/g,'ς')}
function text20(t){if(LABEL20!=='el')return t;return (L20LOOK.get(t)||String(t)).replace(/[A-Za-z][A-Za-z–-]*/g,v=>['km','m','v20'].includes(v)?v:greekText20(v))}
const E20={ok:false};
function prepare20(){if(E20.ok)return;E20.ok=true;
 E20.routes=EXT20.routes.map(x=>({...x,g:geom([x.q],false)}));
 E20.islands=EXT20.islands.map(x=>({...x,g:geom(x.r),areas:x.areas.map(a=>({...a,g:geom(a.r)}))}));
 E20.jp=EXT20.japan.map(x=>({...x,g:geom(x.r)}));
 E20.eez=(EXT20.eez?.zones||[]).map(x=>({...x,g:geom(x.r)}));
}
function extensionGround20(zl){prepare20();const dark=isDark();ctx.save();
 if(LY.eez20){ctx.globalAlpha=.12;for(let i=0;i<E20.eez.length;i++){const z=E20.eez[i];if(!inView(z.g))continue;ctx.fillStyle=i===0?'#337b89':`hsl(${(i*47+170)%360} 50% 48%)`;ctx.fill(P_(z.g,true),'evenodd')}ctx.globalAlpha=.72;ctx.strokeStyle=dark?'#90b8d0':'#3b7f9a';lw(.8);ctx.setLineDash(VIEW==='plane'?[6/view.s,4/view.s]:[6,4]);for(const z of E20.eez)if(inView(z.g))ctx.stroke(P_(z.g,true));ctx.setLineDash([]);ctx.globalAlpha=1}
 if(LY.jp20)for(let i=0;i<E20.jp.length;i++){const d=E20.jp[i];if(!inView(d.g))continue;ctx.fillStyle=`hsla(${i*41} 45% ${dark?45:62}% / .11)`;ctx.fill(P_(d.g,true),'evenodd');ctx.strokeStyle=dark?'#d8c3a0':'#68533c';lw(1.2);ctx.stroke(P_(d.g,true))}
 if(LY.island20)for(const island of E20.islands){if(!inView(island.g))continue;island.areas.forEach((a,i)=>{ctx.fillStyle=`hsla(${i*51+38} 45% ${dark?44:64}% / .26)`;ctx.fill(P_(a.g,true),'evenodd');ctx.strokeStyle=dark?'#b8d0a2':'#65804a';lw(.9);ctx.stroke(P_(a.g,true))})}
 if(LY.transport20)for(const l of E20.routes){if(!inView(l.g))continue;const road=l.kind==='road',bridge=l.kind==='bridge';ctx.strokeStyle=dark?'#202d2b':'#fffdf5';lw(bridge?5:road?3.6:3);ctx.stroke(P_(l.g,false));ctx.strokeStyle=bridge?'#14797e':road?'#b98332':l.kind==='hsr'?'#ac325e':'#795a95';lw(bridge?3:road?2.2:l.kind==='hsr'?1.9:1.4);if(!road&&!bridge)ctx.setLineDash(VIEW==='plane'?[7/view.s,2/view.s]:[7,2]);ctx.stroke(P_(l.g,false));ctx.setLineDash([])}
 if(LY.airports20){ctx.setTransform(dpr,0,0,dpr,0,0);ctx.fillStyle=dark?'#99c3ee':'#235f91';ctx.font='600 17px system-ui';for(const a of EXT20.airports){const p=llToScr(...a.c);if(!p||p[0]<-20||p[0]>W+20||p[1]<-20||p[1]>H+20)continue;ctx.fillText('✈',p[0]-8,p[1]+5)}}
 ctx.restore();
}
function extensionLabels20(put,zl){prepare20();
 if(LY.jp20&&zl>.02)for(const j of E20.jp){const p=llToScr(j.lon,j.lat);if(p)put(p[0],p[1],j.n,j.n==='畿内'?10:12,650,COL.ink)}
 if(LY.island20&&zl>.2)for(const island of E20.islands)for(const a of island.areas){const p=llToScr(...a.c);if(p)put(p[0],p[1],a.n,zl>.8?11:9.5,550,COL.ink2)}
 if(LY.eez20&&zl>.012&&zl<1)for(const z of E20.eez){const p=llToScr(...z.c);if(p)put(p[0],p[1],(LABEL20==='el'?z.el:z.n)+' · ΑΟΖ',9,500,isDark()?'#9dc7dc':'#386e87')}
 if(LY.airports20&&zl>.035)for(const a of EXT20.airports){const p=llToScr(...a.c);if(p)for(const [dx,dy] of [[0,18],[0,-18],[50,0],[-50,0]])if(put(p[0]+dx,p[1]+dy,LABEL20==='el'?a.n:a.zh,10,600,isDark()?'#abd4f3':'#245c8b'))break}
 if(LY.transport20&&zl>.035)for(const l of E20.routes){if(!inView(l.g))continue;const nm=l.n;for(let end=0;end<2;end++){const p=llToScr(...l.ends[end]);if(!p)continue;const suffix=end?' · 终端':' · 起端';for(const [dx,dy] of [[0,end?24:-24],[0,end?-36:36],[70,0],[-70,0]])if(put(p[0]+dx,p[1]+dy,nm+suffix,l.kind==='bridge'?10.5:9.5,600,l.kind==='road'?'#926225':'#71446f'))break}}
}
function macroNames20(put,zl){if(!LY.names20||zl>.4)return;const list=P5.filter(s=>s.c).sort((a,b)=>b.a-a.a);ctx.save();
 for(const s of list){const p=llToScr(s.lon,s.lat);if(!p||p[0]<0||p[0]>W||p[1]<0||p[1]>H)continue;const text=name20(s),fs=s.a>7e5?12.5:s.a>7e4?10.5:8.5;let done=false;
  for(const radius of [0,18,34,52,76,104,138,178,218]){for(const [dx,dy] of radius?[[radius,0],[-radius,0],[0,radius],[0,-radius],[radius*.7,radius*.7],[-radius*.7,-radius*.7]]:[[0,0]]){if(put(p[0]+dx,p[1]+dy,text,fs,600,COL.ink)){if(radius>18){ctx.strokeStyle=isDark()?'rgba(190,205,200,.4)':'rgba(45,65,55,.35)';ctx.lineWidth=.6;ctx.beginPath();ctx.moveTo(...p);ctx.lineTo(p[0]+dx,p[1]+dy);ctx.stroke()}done=true;break}}if(done)break}
 }
 const p=llToScr(111,28);if(p)put(p[0],p[1],LABEL20==='el'?'Νότιον Τσί':'南齐',14,700,COL.seal);ctx.restore();
}
function initExtensions20(){
 Object.assign(LY,{names20:1,transport20:1,airports20:1,island20:1,jp20:1,eez20:1});
 const style=document.createElement('style');style.textContent=`
 #views18{max-width:100%;min-width:0;align-items:center;gap:6px}#views18>*{flex-shrink:0;white-space:nowrap;writing-mode:horizontal-tb!important}#views18 .v18more{min-width:max-content;flex:0 0 auto}#views18 .v20view{position:sticky;left:0;z-index:4;background:var(--panel);border:1px solid var(--celadon);border-radius:20px;padding:8px 12px;font:600 13px var(--body);color:var(--ink)}
 @media(max-width:760px){#views18{display:flex!important;flex-wrap:nowrap!important;overflow-x:auto;overscroll-behavior-x:contain;padding:7px 8px;scrollbar-width:none}#views18 .v18more{margin-left:0}.tools{min-width:0}.app>header{gap:4px}#h1s{max-width:94vw;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
 #atlas20-loading{position:absolute;inset:0;z-index:9;display:grid;place-items:center;background:var(--sea);font:500 14px var(--body);color:var(--ink2)}#atlas20-loading[hidden]{display:none}canvas{image-rendering:auto!important}#extension20{padding:8px 0}#extension20 label{display:flex;align-items:center;gap:7px;padding:4px 0}#label20{font:inherit;max-width:130px}`;document.head.append(style);
 const loading=document.createElement('div');loading.id='atlas20-loading';loading.textContent='正在合成清晰地图…';loading.setAttribute('role','status');wrap.append(loading);
 const panel=document.createElement('details');panel.id='extension20';panel.innerHTML='<summary>新增区划与交通</summary>'+[['names20','宏观政权名称'],['transport20','交广、海岛与罗马干线'],['airports20','拜占庭机场'],['island20','海南·台湾城市与部族'],['jp20','日本八道与畿内'],['eez20','Αποκλειστική Οικονομική Ζώνη · ΑΟΖ']].map(([k,n])=>'<label><input type="checkbox" data-ext20="'+k+'" checked>'+n+'</label>').join('')+'<p class="note">ΑΟΖ：200 海里经济海域示意；领海保留独立开关。八道包含北海道，作为后世区划参照。</p>';
 $('tree').prepend(panel);panel.querySelectorAll('input').forEach(i=>i.onchange=()=>{LY[i.dataset.ext20]=+i.checked;BDIRTY=true;draw()});
 const lang=document.createElement('select');lang.id='label20';lang.setAttribute('aria-label','名称语言');lang.innerHTML='<option value="el" selected>Ελληνικά</option><option value="zh">中文</option><option value="en">English</option>';lang.onchange=()=>{LABEL20=lang.value;BDIRTY=true;buildTree();legend();render();draw();if(CM.J){cLegend();creq()}};document.querySelector('.tools').append(lang);
 const host=$('views18');const sphere=document.createElement('button');sphere.type='button';sphere.id='sphere20';sphere.className='v20view';sphere.textContent='◉ 球形';sphere.setAttribute('aria-label','显示球形');sphere.setAttribute('aria-pressed','false');sphere.onclick=()=>{const fromPlane=VIEW==='plane',c=centerLL();setView(fromPlane?'globe':'plane');if(fromPlane)gv={lon:c[0],lat:c[1],k:1.06};BDIRTY=true;draw();sphere.textContent=VIEW==='globe'?'▱ 平面':'◉ 球形';sphere.setAttribute('aria-pressed',String(VIEW==='globe'))};host.prepend(sphere);
 const shortcuts=[['日本八道','japan'],['交州联通','jiaozhou'],['海南·台湾','islands'],['ΑΟΖ','aoz'],['罗马机场','byzantium']];
 const more=host.querySelector('.v18more');for(const [n,k] of shortcuts){const b=document.createElement('button');b.className='v18';b.type='button';b.textContent=n;b.dataset.extView=k;b.onclick=()=>goto20(k);host.insertBefore(b,more)}
 document.querySelectorAll('.tools #vglobe').forEach(b=>b.textContent='球形');
 // Predecode every retained raster used by any projection. The first visible
 // map is a complete composed frame; repeated resize notifications retain it.
 const metas=[];for(const group of Object.values(D.hs||{}))for(const k of ['alb','eq','eqe'])if(group?.[k])metas.push(group[k]);for(const k of ['alb','eq','eqe'])if(D.rel19?.[k])metas.push(D.rel19[k]);
 const waits=metas.map(m=>{hsImg(m);const o=HSI[m.f];return o?.ok?Promise.resolve():new Promise(resolve=>{if(!o?.img){resolve();return}o.img.addEventListener('load',resolve,{once:true});o.img.addEventListener('error',resolve,{once:true})})});
 Promise.allSettled(waits).then(()=>{READY20=true;BDIRTY=true;BV=null;drawNow();requestAnimationFrame(()=>{loading.hidden=true;document.documentElement.dataset.atlasReady='v20';const key=location.hash.slice(1);if(key)goto20(key)})});
 window.addEventListener('hashchange',()=>goto20(location.hash.slice(1)));
}
function goto20(key){
 if(key.startsWith('city=')){openCity(decodeURIComponent(key.slice(5)),'network');return}
 if(key==='capital')return;
 if(key==='aoz'){LY.eez20=1;setView('globe');gv={lon:120,lat:15,k:2.1};BDIRTY=true;draw();return}
 const b={japan:[[127,29],[148,47]],jiaozhou:[[103.8,19],[114.8,29.5]],islands:[[107,17],[123.4,26.8]],'wei-ne':[[114.5,38],[124.5,44.5]],byzantium:[[18,25],[42,45]]}[key];
 if(b){closeCity();setView('plane');setProj('merc');fitLL(b,25,true);BDIRTY=true;legend();draw()}
}
