const {spawnSync}=require('node:child_process');
for(const [cmd,args] of [[process.execPath,['tools/restore-generated.cjs']],['python3',['tools/stage_public_v26.py']]]){
 const r=spawnSync(cmd,args,{stdio:'inherit'});if(r.status!==0)process.exit(r.status||1);
}
