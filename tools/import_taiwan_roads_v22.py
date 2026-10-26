"""Prepare the official Taiwan road reference for --retrace (scratch only).

Provider: 內政部國土測繪中心, dataset 73232, release 1150409.
License: 政府資料開放授權條款第1版. Source uses EPSG:3826.
"""
from pathlib import Path
from urllib.request import urlopen
import zipfile,io,json,shapefile,numpy as np
from pyproj import CRS,Transformer
ROOT=Path(__file__).resolve().parents[2]/'analysis/rail22';ROOT.mkdir(parents=True,exist_ok=True)
URL='https://opdadm.moi.gov.tw/api/v1/no-auth/resource/api/dataset/03D452C9-B893-4C58-A872-A9D73B58F27F/resource/A6E0ECEB-E8D4-4A7D-B47F-AFC48734F69B/download'
p=ROOT/'taiwan-road-gov.zip'
if not p.exists():p.write_bytes(urlopen(URL,timeout=90).read())
z=zipfile.ZipFile(p);get=lambda ext:io.BytesIO(z.read(next(n for n in z.namelist() if n.endswith(ext))))
r=shapefile.Reader(shp=get('.shp'),dbf=get('.dbf'),encoding='utf-8');prj=z.read(next(n for n in z.namelist() if n.endswith('.prj'))).decode();t=Transformer.from_crs(CRS.from_wkt(prj),'EPSG:4326',always_xy=True);features=[]
for sr in r.iterShapeRecords():
 a=np.asarray(sr.shape.points);x,y=t.transform(a[:,0],a[:,1]);a=np.column_stack([x,y]);parts=list(sr.shape.parts)+[len(a)]
 for s,e in zip(parts,parts[1:]):
  if e-s>1:features.append({'type':'Feature','properties':{},'geometry':{'type':'LineString','coordinates':np.round(a[s:e],7).tolist()}})
(ROOT/'taiwan-gov-roads.json').write_text(json.dumps({'type':'FeatureCollection','features':features},separators=(',',':')))
print('Prepared',len(features),'official road segments')
