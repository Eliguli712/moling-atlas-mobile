"""Build whole-image LODs; retain all native high-resolution originals."""
from pathlib import Path
import json,re,io,base64
from PIL import Image
R=Path(__file__).resolve().parents[1];O=R/'dist';s=(O/'index.html').read_text();images=json.JSONDecoder().raw_decode(s.split('const NQ_IMAGES=',1)[1])[0];out={};report=[]
for name,src in images.items():
 im=Image.open(io.BytesIO(base64.b64decode(src.split(',',1)[1])));levels=[]
 for w in [512,1024,2048]:
  if w>=im.width:continue
  h=round(im.height*w/im.width);small=im.resize((w,h),Image.Resampling.LANCZOS);buf=io.BytesIO();small.save(buf,format='JPEG',quality=88,optimize=True);levels.append(dict(w=w,h=h,src='data:image/jpeg;base64,'+base64.b64encode(buf.getvalue()).decode()))
 levels.append(dict(w=im.width,h=im.height));out[name]=dict(w=im.width,h=im.height,levels=levels);report.append(dict(name=name,width=im.width,height=im.height,native_pixels=im.width*im.height,levels=[{k:v for k,v in l.items() if k!='src'} for l in levels]))
(O/'data/v24_rasters.js').write_text('globalThis.__NQR24='+json.dumps(out,separators=(',',':'))+';');(O/'raster-memory-v24.json').write_text(json.dumps(dict(original_eager_pixels=sum(r['native_pixels'] for r in report),mobile_budget_pixels=24000000,desktop_budget_pixels=36000000,images=report),indent=2));print('Whole-image LOD bundle', (O/'data/v24_rasters.js').stat().st_size, 'bytes')
