"""Stage only SHA-256-pinned public assets into the clean hosting output."""
from pathlib import Path,PurePosixPath
import json,hashlib,shutil
R=Path(__file__).resolve().parents[1];m=json.loads((R/'asset-manifest-v24.json').read_text());dest=R/'out';dest.mkdir(exist_ok=True);names=set()
for a in m['files']:
 name=a['path'];safe=PurePosixPath(name)
 assert not safe.is_absolute() and '..' not in safe.parts
 source=R/'dist'/name;data=source.read_bytes();assert len(data)==a['bytes'] and hashlib.sha256(data).hexdigest()==a['sha256'],name
 target=dest/name;target.parent.mkdir(parents=True,exist_ok=True)
 if not target.exists() or target.stat().st_size!=len(data) or hashlib.sha256(target.read_bytes()).hexdigest()!=a['sha256']:target.write_bytes(data)
 names.add(name)
for p in dest.rglob('*'):
 if p.is_file() and str(p.relative_to(dest)) not in names:p.unlink()
total=sum(a['bytes'] for a in m['files']);assert total<267000000,total
print('Staged',len(names),'verified public assets;',total,'bytes')
