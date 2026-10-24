"""Build a self-contained distribution from the atlas's published v14 assets."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from io import BytesIO
import gzip
import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "site"
OLD = b"https://moling-atlas-mobile.eliguli712.chatgpt.site"
NEW = b"https://eliguli712.github.io/moling-atlas-mobile"
TEXT = {".html", ".js", ".css", ".md", ".json", ".webmanifest", ".csv", ".url", ".txt"}


def download(entry):
    original_html = ROOT / "source-html" / entry["path"]
    compressed_html = original_html.with_suffix(original_html.suffix + ".gz")
    if original_html.suffix == ".html" and compressed_html.is_file():
        data = gzip.decompress(compressed_html.read_bytes())
    elif original_html.suffix == ".html" and original_html.is_file():
        data = original_html.read_bytes()
    else:
        url = OLD.decode() + "/" + quote(entry["path"], safe="/")
        with urlopen(Request(url, headers={"User-Agent": "MolingAtlasPublisher/1.0"}), timeout=90) as response:
            data = response.read()
    if len(data) != entry["bytes"] or sha256(data).hexdigest() != entry["sha256"]:
        raise ValueError("Published v14 asset checksum mismatch: " + entry["path"])
    path = OUTPUT / entry["path"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def rewrite_archive(data, update_checksums=False):
    output = BytesIO()
    with ZipFile(BytesIO(data)) as source, ZipFile(output, "w") as target:
        payloads = {}
        for info in source.infolist():
            payload = source.read(info.filename)
            if Path(info.filename).suffix in TEXT:
                payload = payload.replace(OLD, NEW)
            payloads[info.filename] = payload
        if update_checksums:
            name = "文件核对清单.json"
            manifest = json.loads(payloads[name])
            for item in manifest["files"]:
                payload = payloads.get(item["path"])
                if payload is not None:
                    item["bytes"] = len(payload)
                    item["sha256"] = sha256(payload).hexdigest()
            payloads[name] = json.dumps(manifest, ensure_ascii=False, indent=2).encode()
        for info in source.infolist():
            target.writestr(info, payloads[info.filename])
    result = output.getvalue()
    with ZipFile(BytesIO(result)) as archive:
        if archive.testzip() is not None:
            raise ValueError("Offline archive integrity check failed")
    return result


def rewrite_parts(kind):
    path = OUTPUT / (kind + ".json")
    meta = json.loads(path.read_text())
    data = b"".join((OUTPUT / name).read_bytes() for name in meta["parts"])
    if len(data) != meta["bytes"] or sha256(data).hexdigest() != meta["sha256"]:
        raise ValueError("Offline parts checksum mismatch: " + kind)
    if kind == "final-html":
        data = data.replace(OLD, NEW)
    else:
        data = rewrite_archive(data, update_checksums=True)
    parts = []
    for number, start in enumerate(range(0, len(data), 4194304), 1):
        name = f"{kind}-{number:02}.bin"
        (OUTPUT / name).write_bytes(data[start:start + 4194304])
        parts.append(name)
    for name in set(meta["parts"]) - set(parts):
        (OUTPUT / name).unlink()
    path.write_text(json.dumps({"bytes": len(data), "sha256": sha256(data).hexdigest(), "parts": parts}))


def main():
    entries = json.loads((ROOT / "asset-manifest.json").read_text())["files"]
    OUTPUT.mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=6) as executor:
        list(executor.map(download, entries))
    for path in OUTPUT.iterdir():
        if path.is_file() and path.suffix in TEXT:
            path.write_bytes(path.read_bytes().replace(OLD, NEW))
    for kind in ("final-html", "final-zip"):
        rewrite_parts(kind)
    shortcut = OUTPUT / "nanqi-interactive-bundle.zip"
    shortcut.write_bytes(rewrite_archive(shortcut.read_bytes()))
    (OUTPUT / ".nojekyll").write_text("")
    print(f"Built {len(entries)} checksum-verified public assets for GitHub Pages")


if __name__ == "__main__":
    main()
