/* v21: native-density base caches; symbols and labels remain live. */
var HQ21={entries:[],pixels:0,hits:0,misses:0,epoch:0,tag:'',last:null,maxPixels:12000000};
var RG21;
class AtlasRaster21{
 constructor(){
  this.canvas=document.createElement('canvas');const gl=this.gl=this.canvas.getContext('webgl2',{alpha:true,antialias:false,preserveDrawingBuffer:true});if(!gl)throw Error('WebGL2 unavailable');
  const compile=(type,source)=>{const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s};
  const vs=compile(gl.VERTEX_SHADER,`#version 300 es
  void main(){vec2 p=vec2((gl_VertexID<<1)&2,gl_VertexID&2);gl_Position=vec4(p*2.-1.,0.,1.);}`);
  const fs=compile(gl.FRAGMENT_SHADER,`#version 300 es
  precision highp float;
  uniform vec2 size,centre;uniform float radius,scale,pdist,tilt;uniform int mode,shade;
  uniform sampler2D sea,world,asia,qi;uniform vec4 bs,bw,ba,bq;out vec4 colour;
  const float PI=3.141592653589793;
  vec4 sampleMap(sampler2D tex,vec4 bounds,vec2 ll){float lo=ll.x;while(lo<bounds.x)lo+=360.;while(lo>bounds.x+360.)lo-=360.;vec2 uv=vec2((lo-bounds.x)/bounds.z,(bounds.y-ll.y)/bounds.w);if(any(lessThan(uv,vec2(0.)))||any(greaterThan(uv,vec2(1.))))return vec4(0.);vec4 c=texture(tex,uv);float edge=min(min(uv.x,1.-uv.x),min(uv.y,1.-uv.y));if(bounds.z<359.||bounds.w<179.)c.a*=smoothstep(0.,.015,edge);return c;}
  void main(){vec2 p=vec2(gl_FragCoord.x,size.y-gl_FragCoord.y),ll;
   if(mode==0){float x=(p.x-size.x*.5)/radius,y=-(p.y-size.y*.5)/radius;
    if(tilt>0.){float den=1.-y*sin(tilt)/(pdist-1.);if(den<=0.)discard;float a=cos(tilt)/den;y*=a;x*=a/cos(tilt);}
    float r=length(vec2(x,y)),sc;
    if(pdist>1e6){if(r>1.)discard;sc=r;}else{float arg=1.-r*r*(pdist+1.)/(pdist-1.);if(arg<0.)discard;sc=r<1e-9?0.:(pdist-sqrt(arg))/((pdist-1.)/r+r/(pdist-1.));if(sc>1.)discard;}
    float c=asin(sc),s0=sin(centre.y),c0=cos(centre.y),rr=max(r,1e-9);
    ll.y=asin(clamp(cos(c)*s0+y*sc*c0/rr,-1.,1.));ll.x=centre.x+atan(x*sc,rr*c0*cos(c)-y*s0*sc);
   }else{vec2 km=centre+vec2(p.x-size.x*.5,-p.y+size.y*.5)/scale;ll.x=km.x/6371.+1.9198621771937625;ll.y=mode==1?2.*atan(exp(km.y/6371.))-PI*.5:km.y/6371.;}
   ll*=180./PI;ll.x=mod(ll.x+180.,360.)-180.;
   if(shade==0){colour=sampleMap(sea,bs,ll);return;}
   vec4 c=sampleMap(world,bw,ll),a=sampleMap(asia,ba,ll),q=sampleMap(qi,bq,ll);c=vec4(mix(vec3(1.),c.rgb,c.a),1.);c.rgb=mix(c.rgb,a.rgb,a.a);c.rgb=mix(c.rgb,q.rgb,q.a);colour=c;
  }`);
  this.program=gl.createProgram();gl.attachShader(this.program,vs);gl.attachShader(this.program,fs);gl.linkProgram(this.program);if(!gl.getProgramParameter(this.program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(this.program));
  this.textures=new Map();this.canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();this.lost=true;RG21=null;draw()});this.canvas.addEventListener('webglcontextrestored',()=>{RG21=undefined;draw()});
 }
 render(kind){const gl=this.gl;if(this.lost)return null;const metas=[D.rel19?.eq,D.hs?.world19?.eq,D.hs?.asia?.eq,D.hs?.qi?.eq],images=metas.map(m=>m&&hsImg(m));if(images.some(o=>!o?.ok))return null;
  const width=Math.round(W*dpr),height=Math.round(H*dpr);if(this.canvas.width!==width||this.canvas.height!==height){this.canvas.width=width;this.canvas.height=height}gl.viewport(0,0,width,height);gl.useProgram(this.program);
  const u=n=>gl.getUniformLocation(this.program,n);gl.uniform2f(u('size'),width,height);gl.uniform1i(u('mode'),VIEW==='globe'?0:PROJ==='merc'?1:2);gl.uniform1i(u('shade'),kind==='shade'?1:0);
  gl.uniform2f(u('centre'),VIEW==='globe'?gv.lon*RAD:view.cx,VIEW==='globe'?gv.lat*RAD:view.cy);gl.uniform1f(u('radius'),VIEW==='globe'?gR()*dpr:1);gl.uniform1f(u('scale'),view.s*dpr);gl.uniform1f(u('pdist'),gPd());gl.uniform1f(u('tilt'),VIEW==='globe'&&GP==='persp'?TILT*RAD:0);
  for(let i=0;i<4;i++){const m=metas[i],im=images[i].img;gl.activeTexture(gl.TEXTURE0+i);let t=this.textures.get(m.f);if(!t){t=gl.createTexture();this.textures.set(m.f,t);gl.bindTexture(gl.TEXTURE_2D,t);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,im)}else gl.bindTexture(gl.TEXTURE_2D,t);gl.uniform1i(u(['sea','world','asia','qi'][i]),i);gl.uniform4f(u(['bs','bw','ba','bq'][i]),m.lon0,m.lat0,m.W*m.DL,m.H*m.DL)}
  gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT);gl.drawArrays(gl.TRIANGLES,0,3);return this.canvas;
 }
}
function raster21Draw(kind){if(!(VIEW==='globe'||PROJ==='merc'||PROJ==='eqc'))return false;if(kind==='sea'&&LY.sea19===0)return true;if(RG21===false)return false;try{if(!RG21)RG21=new AtlasRaster21();const c=RG21.render(kind);if(!c)return false;ctx.save();ctx.setTransform(dpr,0,0,dpr,0,0);ctx.globalAlpha=kind==='sea'?(isDark()?.5:.95):LY.hsk*(isDark()?.6:1);if(kind==='shade')ctx.globalCompositeOperation='multiply';ctx.drawImage(c,0,0,W,H);ctx.restore();return true}catch(e){if(!String(e).includes('WebGL2 unavailable'))console.warn('GPU 地图底图回退',e);RG21=false;return false}}
function hqFits21(e){if(e.tag!==HQ21.tag||e.dpr!==dpr)return false;const k=view.s/e.s,x=W/2+(e.cx-view.cx)*view.s-e.bw*k/2,y=H/2-(e.cy-view.cy)*view.s-e.bh*k/2;return k<=1.000001&&k>=.78&&x<=-.25&&y<=-.25&&x+e.bw*k>=W+.25&&y+e.bh*k>=H+.25}
function drawNow(){if(!W||!READY20||!HQ21)return;const t=performance.now(),moving=FAST;FAST=false;try{
 if(VIEW==='globe'){FAST=moving;ctx=ctx0;drawStatic();drawDynLayers();FAST=false;BV=null;HQ21.last=null;Object.assign($('map').dataset,{cacheDensity:String(dpr),cacheScale:'1'})}else{
  const ready=Object.entries(LZ).map(([k,x])=>k+':'+(x.d?'ok':x.err?'err':'loading')).join(','),tag=[W,H,dpr,PROJ,isDark(),JSON.stringify(LY),JSON.stringify(NX.layers),sel.type,sel.id,READY20,ready,!!FINAL.land,!!FINAL.relief,Object.values(HSI).filter(x=>x.ok).length].join('|');
  if(tag!==HQ21.tag){HQ21.tag=tag;HQ21.entries=[];HQ21.pixels=0}
  const at=[view.cx,view.cy,view.s].join(',');if(BDIRTY&&HQ21.last===at){HQ21.entries=[];HQ21.pixels=0}HQ21.last=at;
  let e=HQ21.entries.find(hqFits21);if(e){HQ21.hits++;HQ21.entries.splice(HQ21.entries.indexOf(e),1);HQ21.entries.push(e)}else{
   HQ21.misses++;const s=view.s;view.s=Math.pow(2,Math.ceil(Math.log2(s)*8)/8);try{renderBase(vkey())}finally{view.s=s}
   const c=document.createElement('canvas');c.width=BASE.width;c.height=BASE.height;c.getContext('2d').drawImage(BASE,0,0);e={...BV,canvas:c,dpr,tag:HQ21.tag};HQ21.entries.push(e);HQ21.pixels+=c.width*c.height;while(HQ21.entries.length>1&&(HQ21.entries.length>4||HQ21.pixels>HQ21.maxPixels)){const q=HQ21.entries.shift();HQ21.pixels-=q.canvas.width*q.canvas.height}
  }
  const k=view.s/e.s,x=W/2+(e.cx-view.cx)*view.s-e.bw*k/2,y=H/2-(e.cy-view.cy)*view.s-e.bh*k/2;ctx0.setTransform(dpr,0,0,dpr,0,0);ctx0.imageSmoothingEnabled=true;ctx0.imageSmoothingQuality='high';ctx0.drawImage(e.canvas,x,y,e.bw*k,e.bh*k);BV=e;BDIRTY=false;drawDynLayers();$('map').dataset.cacheDensity=String(dpr/k);$('map').dataset.cacheScale=String(k);
 }
 Object.assign($('map').dataset,{frameMode:'live',renderEngine:RG21&&RG21!==false?'webgl2':'canvas2d',frameMs:(performance.now()-t).toFixed(1),cacheHits:String(HQ21.hits),cacheMisses:String(HQ21.misses),cachePixels:String(HQ21.pixels)});
 }finally{FAST=moving}}
function cSnapOK(){return false}
function cSnapTake(){CSV=null}
function drawCityGroundCached(g,J,tab){const v=CM.v,st=CITY_BASE_STATE,tag=[J.k,tab,CM.W,CM.H,CM.dpr,isDark(),CM.scenario,CM.tracks.ports,CM.tracks.ferries].join('|');let k=st?v.s/st.s:1,x=st?CM.W/2+(st.cx-v.cx)*v.s-st.w*k/2:1,y=st?CM.H/2+(st.cy-v.cy)*v.s-st.h*k/2:1;
 if(!(st&&st.tag===tag&&k<=1.000001&&k>.78&&x<=0&&y<=0&&x+st.w*k>=CM.W&&y+st.h*k>=CM.H)){
  if(!CITY_BASE)CITY_BASE=document.createElement('canvas');const w0=CM.W,h0=CM.H,s0=v.s,w=Math.ceil(w0*Math.min(1.4,Math.sqrt(12000000/(w0*h0*CM.dpr*CM.dpr)))),h=Math.ceil(h0*Math.min(1.4,Math.sqrt(12000000/(w0*h0*CM.dpr*CM.dpr))));CITY_BASE.width=Math.round(w*CM.dpr);CITY_BASE.height=Math.round(h*CM.dpr);const bg=CITY_BASE.getContext('2d');bg.setTransform(CM.dpr,0,0,CM.dpr,0,0);bg.fillStyle=isDark()?'#232a27':'#f3f1ea';bg.fillRect(0,0,w,h);CM.W=w;CM.H=h;v.s=Math.pow(2,Math.ceil(Math.log2(s0)*8)/8);try{drawCityGround(bg,J,tab);CITY_BASE_STATE={tag,w,h,s:v.s,cx:v.cx,cy:v.cy}}finally{CM.W=w0;CM.H=h0;v.s=s0}const n=CITY_BASE_STATE;k=v.s/n.s;x=CM.W/2+(n.cx-v.cx)*v.s-n.w*k/2;y=CM.H/2+(n.cy-v.cy)*v.s-n.h*k/2;
 }
 const n=CITY_BASE_STATE;g.save();g.setTransform(CM.dpr,0,0,CM.dpr,0,0);g.imageSmoothingQuality='high';g.drawImage(CITY_BASE,x,y,n.w*k,n.h*k);g.restore();ccv.dataset.cacheDensity=String(CM.dpr/k);
}
var SPHERE21=new WeakMap();
var TEXT21=new Map();
function PA(g){if(PROJ==='alb'||PROJ==='eqe')return PA20(g);if(g.pp[PROJ])return g.pp[PROJ];const seam=g.ll.some(r=>{for(let i=2;i<r.length;i+=2)if(Math.abs(dl0(r[i])-dl0(r[i-2]))>Math.PI)return true;return false});if(!seam)return PA20(g);
 const fill=new Path2D(),outline=new Path2D(),period=2*Math.PI*6371,limit=Math.PI*6371,b=[-limit,-20020,limit,20020];
 const clip=(points,x,less)=>{const out=[];if(!points.length)return out;let a=points[points.length-1],ina=less?a[0]<=x:a[0]>=x;for(const c of points){const inc=less?c[0]<=x:c[0]>=x;if(ina!==inc){const t=(x-a[0])/(c[0]-a[0]);out.push([x,a[1]+(c[1]-a[1])*t])}if(inc)out.push(c);a=c;ina=inc}return out};
 for(const r of g.ll){const pts=[];let last;for(let i=0;i<r.length;i+=2){let x=dl0(r[i])*6371;if(last!==undefined){while(x-last>limit)x-=period;while(x-last< -limit)x+=period}pts.push([x,pf(r[i],r[i+1])[1]]);last=x}
  if(pts.length<2)continue;const pole=g.closed&&Math.abs(pts[pts.length-1][0]-pts[0][0])>period*.9;
  const polygon=pts.slice();if(pole){const north=r.reduce((v,x,i)=>i%2?v+x:v,0)/(r.length/2)>0,y=pf(0,north?85:-85)[1];polygon.push([pts[pts.length-1][0],y],[pts[0][0],y])}
  for(let shift=-1;shift<=1;shift++){let a=polygon.map(p=>[p[0]+shift*period,p[1]]);a=clip(clip(a,-limit,false),limit,true);if(g.closed&&a.length>2)for(let repeat=-1;repeat<=1;repeat++){fill.moveTo(a[0][0]+repeat*period,a[0][1]);for(let i=1;i<a.length;i++)fill.lineTo(a[i][0]+repeat*period,a[i][1]);fill.closePath()}
   for(let i=1;i<pts.length;i++){let a=[pts[i-1][0]+shift*period,pts[i-1][1]],c=[pts[i][0]+shift*period,pts[i][1]];if(a[0]< -limit&&c[0]< -limit||a[0]>limit&&c[0]>limit)continue;for(const edge of [-limit,limit])if((a[0]<edge)!==(c[0]<edge)){const t=(edge-a[0])/(c[0]-a[0]),p=[edge,a[1]+(c[1]-a[1])*t];if(a[0]<-limit||a[0]>limit)a=p;else c=p}for(let repeat=-1;repeat<=1;repeat++){outline.moveTo(a[0]+repeat*period,a[1]);outline.lineTo(c[0]+repeat*period,c[1])}}
  }
 }
 g._outline21=g._outline21||{};g._outline21[PROJ]=outline;g.pp[PROJ]=g.closed?fill:outline;g.bb[PROJ]=b;return g.pp[PROJ];
}
function outline21(g){const path=P_(g,true);return VIEW==='plane'&&g._outline21?.[PROJ]||path}
function worldLabel21(occ,done,grid,ff,x,y,txt,size,weight,col){txt=text20(txt);if(done.has(txt)||!Number.isFinite(x)||!Number.isFinite(y))return false;const font=`${weight} ${size}px ${ff}`,key=font+'|'+txt;ctx.font=font;let w=TEXT21.get(key);if(w===undefined){w=ctx.measureText(txt).width;if(TEXT21.size>16000)TEXT21.clear();TEXT21.set(key,w)}const h=size,b=[x-w/2-2,y-h/2-2,x+w/2+2,y+h/2+2];if(b[0]<4||b[1]<4||b[2]>W-4||b[3]>H-4)return false;const x0=Math.floor(b[0]/64),x1=Math.floor(b[2]/64),y0=Math.floor(b[1]/64),y1=Math.floor(b[3]/64),seen=new Set();for(let j=y0;j<=y1;j++)for(let i=x0;i<=x1;i++)for(const o of grid.get(i+','+j)||[]){if(seen.has(o))continue;seen.add(o);if(!(b[2]<o[0]||o[2]<b[0]||b[3]<o[1]||o[3]<b[1]))return false}for(let j=y0;j<=y1;j++)for(let i=x0;i<=x1;i++){const key=i+','+j;if(!grid.has(key))grid.set(key,[]);grid.get(key).push(b)}occ.push(b);done.add(txt);ctx.lineWidth=3;ctx.strokeStyle=COL.panel;ctx.strokeText(txt,x-w/2,y+h*.36);ctx.fillStyle=col;ctx.fillText(txt,x-w/2,y+h*.36);return true}
function sphereRings21(ll){let levels=SPHERE21.get(ll);if(!levels){levels=new Map();SPHERE21.set(ll,levels)}const tolerance=Math.pow(2,Math.floor(Math.log2(.3/(gR()*Math.max(1,(gPd()+1)/(gPd()-1))))));if(levels.has(tolerance))return levels.get(tolerance);
 const rings=ll.map(r=>{const n=r.length/2,a=new Float64Array(n*5);for(let i=0;i<n;i++){const lo=r[i*2]*RAD,la=r[i*2+1]*RAD,cp=Math.cos(la);a.set([cp*Math.cos(lo),cp*Math.sin(lo),Math.sin(la),r[i*2],r[i*2+1]],i*5)}if(n<8)return a;const keep=new Uint8Array(n);keep[0]=keep[n-1]=1;const stack=[[0,n-1]],t2=tolerance*tolerance;while(stack.length){const [s,e]=stack.pop();let max=t2,at=-1;const x=a[e*5]-a[s*5],y=a[e*5+1]-a[s*5+1],z=a[e*5+2]-a[s*5+2],d=x*x+y*y+z*z;for(let i=s+1;i<e;i++){const u=a[i*5]-a[s*5],v=a[i*5+1]-a[s*5+1],w=a[i*5+2]-a[s*5+2],q=d?Math.max(0,Math.min(1,(u*x+v*y+w*z)/d)):0,dd=(u-q*x)**2+(v-q*y)**2+(w-q*z)**2;if(dd>max){max=dd;at=i}}if(at>=0){keep[at]=1;stack.push([s,at],[at,e])}}const out=[];for(let i=0;i<n;i++)if(keep[i])out.push(...a.subarray(i*5,i*5+5));return Float64Array.from(out)});if(levels.size>=4)levels.delete(levels.keys().next().value);levels.set(tolerance,rings);return rings;
}
function gpath(ll,closed){const p=new Path2D(),R=gR(),P=gPd(),ch=1/P,sh=Math.sqrt(1-ch*ch),lo=gv.lon*RAD,la=gv.lat*RAD,sl=Math.sin(lo),cl=Math.cos(lo),sp=Math.sin(la),cp=Math.cos(la),tw=TILT*RAD,st=Math.sin(tw),ct=Math.cos(tw);let al=gv.lon+180;if(al>180)al-=360;const ala=-gv.lat;
 for(const [ri,r] of sphereRings21(ll).entries()){let pen=false,cnt=0,hid=0,b0=1e9,b1=1e9,b2=-1e9,b3=-1e9;for(let i=0;i<r.length;i+=5){const front=r[i]*cl+r[i+1]*sl;let sx=-r[i]*sl+r[i+1]*cl,sy=cp*r[i+2]-sp*front,cc=sp*r[i+2]+cp*front,vis=cc-ch;if(closed){if(vis<0)hid=1;b0=Math.min(b0,r[i+3]);b2=Math.max(b2,r[i+3]);b1=Math.min(b1,r[i+4]);b3=Math.max(b3,r[i+4])}if(vis<0&&!closed){pen=false;continue}if(cc<ch){const h=Math.hypot(sx,sy)||1;sx=sx/h*sh;sy=sy/h*sh;cc=ch}const K=P>1e6?1:(P-1)/(P-cc);let x=K*sx,y=K*sy;if(GP==='persp'&&TILT>0){const a=y*st/(P-1)+ct;if(a<=.02){pen=false;continue}x=x*ct/a;y/=a}const X=W/2+R*x,Y=H/2-R*y;if(pen)p.lineTo(X,Y);else{p.moveTo(X,Y);pen=true}cnt++}if(closed&&cnt)p.closePath();if(closed&&hid&&cnt&&al>=b0&&al<=b2&&ala>=b1&&ala<=b3&&pipLL19(ll[ri],al,ala))gWrap19(p,ll[ri],R)}return p;
}
