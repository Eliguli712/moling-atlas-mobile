"""Apply the bounded v23-r2 runtime repair to an existing v23 index."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
page = ROOT / 'dist/index.html'
source = page.read_text()
start = source.index('/* v23: land-constrained')
end = source.index('window.__atlas={', start)
source = source[:start] + (ROOT / 'tools/runtime-v23.js').read_text() + '\n' + source[end:]
source = source.replace('v=23-r1', 'v=23-r2')
page.write_text(source)
print('Installed v23-r2 runtime and cache revision')
