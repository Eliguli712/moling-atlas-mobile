const assert=require('node:assert/strict');let W=430,H=600,dpr=3,gv={lon:99,lat:31,k:1},GP='ortho',ALT=3000,TILT=0;const RAD=Math.PI/180,RE=6371,MOBILE24=true,MESH25={tag:'',meshes:new Map()};const scrToLL=(x,y)=>ginv(x,y);const llToScr=(lo,la)=>{const q=gproj(lo,la);return q[2]>=0?q:null};function cameraTag24(){return [W,H,gv.lon,gv.lat,gv.k,GP,ALT,TILT].join('|')}
function gPd(){return GP==='persp'?1+ALT/6371:1e7}
function gNorm(){const P=gPd();if(P>1e6)return 1;const ch=1/P,sh=Math.sqrt(1-ch*ch),Kh=(P-1)/(P-ch);return 1/(Kh*sh)}
const gR=()=>Math.min(W,H)*0.46*gv.k*gNorm();     // px per Earth radius at the centre of the view

function gcore(lon,lat){const l=(lon-gv.lon)*RAD,ph=lat*RAD,p0=gv.lat*RAD;const cp=Math.cos(ph),sp=Math.sin(ph),c0=Math.cos(p0),s0=Math.sin(p0),cl=Math.cos(l);
  let sx=cp*Math.sin(l),sy=c0*sp-s0*cp*cl,cc=s0*sp+c0*cp*cl;const P=gPd(),ch=1/P;let vis=cc-ch;
  if(cc<ch){const sh=Math.sqrt(1-ch*ch),h=Math.hypot(sx,sy)||1;sx=sx/h*sh;sy=sy/h*sh;cc=ch}
  const K=P>1e6?1:(P-1)/(P-cc);let x=K*sx,y=K*sy;
  if(GP==='persp'&&TILT>0){const w=TILT*RAD,A=y*Math.sin(w)/(P-1)+Math.cos(w);if(A<=0.02)return [x,y,-1];x=x*Math.cos(w)/A;y=y/A}
  return [x,y,vis]}
function gproj(lon,lat){const [x,y,v]=gcore(lon,lat);const R=gR();return [W/2+R*x,H/2-R*y,v]}
function ginv(px,py){const R=gR();let x=(px-W/2)/R,y=-(py-H/2)/R;const P=gPd(),p0=gv.lat*RAD;
  if(GP==='persp'&&TILT>0){const w=TILT*RAD,d=1-y*Math.sin(w)/(P-1);if(d<=0)return null;const A=Math.cos(w)/d;y=y*A;x=x*A/Math.cos(w)}
  const r=Math.hypot(x,y);if(r<1e-12)return [gv.lon,gv.lat];let sc;
  if(P>1e6){if(r>1)return null;sc=r}else{const arg=1-r*r*(P+1)/(P-1);if(arg<0)return null;sc=(P-Math.sqrt(arg))/((P-1)/r+r/(P-1));if(sc>1)return null}
  const c=Math.asin(sc);const lat=Math.asin(Math.cos(c)*Math.sin(p0)+y*sc*Math.cos(p0)/r)/RAD;let lon=gv.lon+Math.atan2(x*sc,r*Math.cos(p0)*Math.cos(c)-y*Math.sin(p0)*sc)/RAD;while(lon>180)lon-=360;while(lon<-180)lon+=360;return [lon,lat]}

function rasterMesh25(m,img){const tag=cameraTag24();if(MESH25.tag!==tag){MESH25.tag=tag;MESH25.meshes.clear()}const key=[m.f,img.width,img.height].join('|');if(MESH25.meshes.has(key))return MESH25.meshes.get(key);const triangles=[],cache=new Map(),wrap=m.W*m.DL>359,step=MOBILE24?56:64,maxTriangles=MOBILE24?5000:9000;
 const sample=(x,y)=>{const k=x+','+y;if(cache.has(k))return cache.get(k);const ll=scrToLL(x,y);const p=ll?{x,y,u:(ll[0]-m.lon0)/(m.W*m.DL)*img.width,v:(m.lat0-ll[1])/(m.H*m.DL)*img.height}:null;cache.set(k,p);return p};
 const emit=(a,b,c)=>{if(!a||!b||!c)return;const p=[a,b,c].map(q=>({...q}));if(wrap&&Math.max(...p.map(q=>q.u))-Math.min(...p.map(q=>q.u))>img.width/2)for(const q of p)if(q.u<img.width/2)q.u+=img.width;if(Math.max(...p.map(q=>q.v))<0||Math.min(...p.map(q=>q.v))>img.height||(!wrap&&(Math.max(...p.map(q=>q.u))<0||Math.min(...p.map(q=>q.u))>img.width)))return;triangles.push(p)};
 const edge=(a,b)=>{let good=a,bad=b;for(let i=0;i<10;i++){const mid={x:(good.x+bad.x)/2,y:(good.y+bad.y)/2},p=sample(mid.x,mid.y);if(p)good=p;else bad=mid}return good};
 const cell=(x0,y0,x1,y1,depth)=>{const A=sample(x0,y0),B=sample(x1,y0),C=sample(x1,y1),E=sample(x0,y1),cx=(x0+x1)/2,cy=(y0+y1)/2,M=sample(cx,cy),pts=[A,B,C,E],n=pts.filter(Boolean).length;let refine=n!==4;
  if(n===4&&M){let us=pts.map(p=>p.u);if(wrap&&Math.max(...us)-Math.min(...us)>img.width/2)us=us.map(u=>u<img.width/2?u+img.width:u);const u=us.reduce((a,b)=>a+b,0)/4,v=pts.reduce((a,b)=>a+b.v,0)/4,q=llToScr(m.lon0+u/img.width*m.W*m.DL,m.lat0-v/img.height*m.H*m.DL);refine=!q||Math.hypot(q[0]-cx,q[1]-cy)>1.1}
  if(depth<3&&triangles.length<maxTriangles-32&&refine&&(n||M)){cell(x0,y0,cx,cy,depth+1);cell(cx,y0,x1,cy,depth+1);cell(cx,cy,x1,y1,depth+1);cell(x0,cy,cx,y1,depth+1);return}
  if(n===4){emit(A,B,C);emit(A,C,E);return}if(!n)return;const corners=[{x:x0,y:y0},{x:x1,y:y0},{x:x1,y:y1},{x:x0,y:y1}],poly=[];for(let i=0;i<4;i++){const j=(i+1)%4;if(pts[i])poly.push(pts[i]);if(!!pts[i]!==!!pts[j])poly.push(pts[i]?edge(pts[i],corners[j]):edge(pts[j],corners[i]))}for(let i=1;i+1<poly.length;i++)emit(poly[0],poly[i],poly[i+1])};
 for(let y=0;y<H;y+=step)for(let x=0;x<W;x+=step)cell(x,y,Math.min(W,x+step),Math.min(H,y+step),0);const out={triangles,samples:cache.size};MESH25.meshes.set(key,out);return out}

const results=[];for(const gp of ['ortho','persp'])for(const k of [1,18,100,3000]){GP=gp;TILT=gp==='persp'?65:0;gv.k=k;const v=rasterMesh25({f:'global',W:3600,H:1800,DL:.1,lon0:-180,lat0:90},{width:3600,height:1800});assert(v.triangles.length>0);assert(v.triangles.length<5000);for(const tri of v.triangles)for(const p of tri)assert([p.x,p.y,p.u,p.v].every(Number.isFinite));results.push({projection:gp,zoom:k,triangles:v.triangles.length,inverse_samples:v.samples})}console.log(JSON.stringify(results,null,2));require('node:fs').writeFileSync('analysis-v25/mesh-results.json',JSON.stringify(results,null,2));