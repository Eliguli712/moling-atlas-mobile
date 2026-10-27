"""Load immutable atlas inputs, including generated files retained in Git."""
from pathlib import Path
import base64,gzip,json,subprocess,ast,pickle,copy
R=Path(__file__).resolve().parents[1];O=R/'dist';T=R/'analysis-v24';T.mkdir(exist_ok=True)
def generated_at(commit,path):
 m=json.loads(subprocess.check_output(['git','show',commit+':tools/generated-assets.json'],cwd=R));f=next((v for v in m['files'] if v['path']==path),None)
 if f is None:return subprocess.check_output(['git','show',commit+':'+path],cwd=R)
 b=b''.join(subprocess.check_output(['git','show',commit+':generated-parts/'+n],cwd=R) for n in f['parts'])
 if f.get('encoding')=='gzip':b=gzip.decompress(b)
 import hashlib
 assert len(b)==f['bytes'] and hashlib.sha256(b).hexdigest()==f['sha256'];return b
from revise_atlas_v20 import decode,encode,dumps

def baseline():
 cache=T/'base-v23-r2.pkl'
 if cache.exists():return pickle.load(cache.open('rb'))
 commit='88b84d58a45fc128329f6a8c5cbda434c2c77968'
 D=decode(json.loads(generated_at(commit,'dist/data/v23_d.js').decode().split('=',1)[1].strip().rstrip(';')));A={};F={}
 for name in [*[f'v23_a4_{i}.js' for i in range(5)],*[f'v23_a5_{i}.js' for i in range(4)],'v23_extra.js']:
  prefix,body=generated_at(commit,'dist/data/'+name).decode().split('=',1);data=json.loads(body.strip().rstrip(';'));F[name]=(prefix,data);A.update(data)
 C=decode(A['l_city.json']);pickle.dump((D,A,F,C),cache.open('wb'));return D,A,F,C

def oldD():
 p=T/'legacy-v22-d.pkl'
 if p.exists():return pickle.load(p.open('rb'))
 b=generated_at('c377eebcdac17b11c36ef2cf1fd094d92e8dee70','dist/data/v22_d.js').decode();d=decode(json.loads(b.split('=',1)[1].strip().rstrip(';')));pickle.dump(d,p.open('wb'));return d

def planning_namespace(D):
 # Import pure geometry helpers without executing the historical rebuild.
 src=(R/'tools/revise_atlas_v23.py').read_text();tree=ast.parse(src);keep=[]
 for n in tree.body:
  if isinstance(n,(ast.Import,ast.ImportFrom)) or isinstance(n,(ast.FunctionDef,ast.ClassDef)):keep.append(n)
 ns={'__file__':str(R/'tools/revise_atlas_v23.py'),'D':D,'P':D['proj']};exec(compile(ast.Module(body=keep,type_ignores=[]),str(R/'tools/revise_atlas_v23.py'),'exec'),ns);return ns
if __name__=='__main__':
 D,A,F,C=baseline();print('Assets',len(A),'files',list(F),'cities',len(C['city']))
 for s in C['city']:
  if s['k'].startswith('qv20_') or s['k']=='q0065' or s['k']=='wdf268c':
   c=decode(A['c/'+s['k']+'.json']);print(s['k'],s['n'],list(c.keys()),'w',c['w'],'origin',c['o'],'lt',c.get('lt'),'metro',c['metro']);print('lr sample',str(c.get('lrt'))[:500]);print('line sample',str(c['ml'][0] if c['ml'] else None)[:400]);print('terrain',str(c.get('terrain'))[:200]);print('city center',s.get('lon'),s.get('lat'))
 print('islands',[(v.get('n'),v.keys()) for v in D['v20_ext']['islands']])
