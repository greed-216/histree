import {readFile,writeFile,mkdtemp,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {spawnSync} from 'node:child_process';
const directory=await mkdtemp(join(tmpdir(),'histree-smoke-'));
try {
 const data=JSON.parse(await readFile(new URL('../apps/web/src/data/history-scroll.json',import.meta.url),'utf8'));
 const manifest=join(directory,'manifest.json');await writeFile(manifest,JSON.stringify({scroll:data.panels}));
 const result=spawnSync(process.execPath,['deploy/ecs/verify.mjs',process.env.E2E_WEB_URL || 'http://127.0.0.1:3000',manifest],{stdio:'inherit'});
 if(result.status!==0)process.exitCode=1;
}finally{await rm(directory,{recursive:true,force:true});}
