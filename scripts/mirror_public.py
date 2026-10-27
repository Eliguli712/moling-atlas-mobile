"""Build GitHub Pages from the exact SHA-256-pinned v23 distribution."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from io import BytesIO
from pathlib import Path,PurePosixPath
from urllib.request import Request,urlopen
from urllib.parse import quote
from zipfile import ZipFile
import json,time
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'site'
def verified(data,entry):
    if len(data)!=entry['bytes'] or sha256(data).hexdigest()!=entry['sha256']:
        raise ValueError('Checksum mismatch: '+entry['path'])
    return data
def main():
    manifest=json.loads((ROOT/'asset-manifest.json').read_text());source=manifest['source'].rstrip('/')
    def save(entry,data):
        dest=OUT/entry['path'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(verified(data,entry))
    def download(entry):
        name=entry['path'];path=PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts:raise ValueError('Invalid asset path')
        for local in [ROOT/'dist'/name,ROOT/'source-html'/name]:
            if local.is_file():
                data=local.read_bytes()
                if len(data)==entry['bytes'] and sha256(data).hexdigest()==entry['sha256']:save(entry,data);return
        for attempt in range(3):
            try:
                req=Request(source+'/'+quote(name,safe='/'),headers={'User-Agent':'MolingAtlasPublisher/v23'})
                with urlopen(req,timeout=120) as response:data=response.read()
                save(entry,data);return
            except Exception:
                if attempt==2:raise
                time.sleep(2+attempt)
    OUT.mkdir(exist_ok=True)
    # Sites adds its hosting shell to HTML responses. Recover original HTML
    # from the already checksum-verified offline ZIP; other assets stay raw.
    binary=[e for e in manifest['files'] if not e['path'].endswith('.html')]
    with ThreadPoolExecutor(max_workers=6) as executor:list(executor.map(download,binary))
    meta=json.loads((OUT/'final-zip.json').read_text());data=b''.join((OUT/n).read_bytes() for n in meta['parts'])
    if len(data)!=meta['bytes'] or sha256(data).hexdigest()!=meta['sha256']:raise ValueError('Offline archive checksum mismatch')
    with ZipFile(BytesIO(data)) as archive:
        if archive.testzip():raise ValueError('Offline archive CRC mismatch')
        for entry in manifest['files']:
            if entry['path'].endswith('.html'):save(entry,archive.read(entry['path']))
    (OUT/'.nojekyll').write_text('')
    print('Built',len(manifest['files']),'verified v23 assets')
if __name__=='__main__':main()
