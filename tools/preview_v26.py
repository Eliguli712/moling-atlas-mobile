"""Stage a disposable mobile QA page; stage_public_v26 removes it for release."""
from pathlib import Path
import shutil
R=Path(__file__).resolve().parents[1];O=R/'dist';out=R/'out';out.mkdir(exist_ok=True)
for p in [O/'index.html',O/'static.html',O/'sw.js',O/'manifest.webmanifest',*O.glob('icon-*.png'),*O.glob('static-*-v26.svg'),*(O/'data').glob('v26*.js')]:
 t=out/p.relative_to(O);t.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,t)
s=(O/'index.html').read_text().replace('window.devicePixelRatio||1','3');s=s.replace('initExtensions20();',(R/'tools/qa-v26.js').read_text()+'\ninitExtensions20();');(out/'qa26.html').write_text(s)
(out/'mobile-qa26.html').write_text('<!doctype html><meta charset="utf-8"><title>Atlas v26 mobile QA · 430 CSS px · application DPR cap</title><style>body{margin:0;background:#ddd}iframe{display:block;width:430px;height:820px;border:0}</style><iframe title="mobile atlas" src="qa26.html"></iframe>')
print('Staged disposable 430 CSS px mobile QA fixture')
