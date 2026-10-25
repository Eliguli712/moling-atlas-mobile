"""Build GitHub Pages from the exact SHA-256-pinned v20 distribution."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path,PurePosixPath
from urllib.request import Request,urlopen
from urllib.parse import quote
import json,time
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'site'
def main():
    manifest=json.loads((ROOT/'asset-manifest.json').read_text())
    source=manifest['source'].rstrip('/')
    def download(entry):
        name=entry['path'];path=PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts:raise ValueError('Invalid asset path')
        data=None
        # Prefer an exact local source copy when one is present. The old v14
        # snapshot is retained for history and never overrides a v20 asset.
        for local in [ROOT/'dist'/name,ROOT/'source-html'/name]:
            if local.is_file():
                raw=local.read_bytes()
                if len(raw)==entry['bytes'] and sha256(raw).hexdigest()==entry['sha256']:data=raw;break
        if data is None:
            for attempt in range(3):
                try:
                    req=Request(source+'/'+quote(name,safe='/'),headers={'User-Agent':'MolingAtlasPublisher/v20'})
                    with urlopen(req,timeout=120) as response:data=response.read()
                    if len(data)!=entry['bytes'] or sha256(data).hexdigest()!=entry['sha256']:raise ValueError('Checksum mismatch: '+name)
                    break
                except Exception:
                    if attempt==2:raise
                    time.sleep(2+attempt)
        dest=OUT/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    OUT.mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=6) as executor:list(executor.map(download,manifest['files']))
    (OUT/'.nojekyll').write_text('')
    print('Built',len(manifest['files']),'verified v20 assets')
if __name__=='__main__':main()
