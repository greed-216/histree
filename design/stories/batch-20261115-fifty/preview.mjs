// Read-only local preview of the built web app and this batch's actual image bytes.
import http from 'node:http';
import { readFile, stat, readdir } from 'node:fs/promises';
import { resolve, basename, extname } from 'node:path';
const root = resolve(import.meta.dirname, '../../..');
const dist = resolve(root, 'apps/web/dist');
const assets = resolve(root, 'artifacts/stories-fifty-20261115/upload');
const legacy=new Map();
async function scan(dir) {
  for(const entry of await readdir(dir,{withFileTypes:true})) {
    const p=resolve(dir,entry.name);
    if(entry.isDirectory())await scan(p);
    else if(/^[a-f0-9]{64}\.webp$/.test(entry.name))legacy.set(entry.name,p);
  }
}
if(process.argv[2])await scan(resolve(process.argv[2]));
const types = { '.html':'text/html', '.js':'text/javascript', '.css':'text/css', '.png':'image/png', '.webp':'image/webp', '.svg':'image/svg+xml', '.json':'application/json' };
const server = http.createServer(async (req,res) => {
  try {
    if (req.method !== 'GET') { res.writeHead(405).end(); return; }
    const url = new URL(req.url, 'http://localhost');
    let file;
    if (url.pathname.startsWith('/api/')) {
      if (url.pathname.startsWith('/api/v1/media/images/')) {
        const name=basename(url.pathname);
        if (/^[a-f0-9]{64}\.(png|webp)$/.test(name)) {
          try { file=resolve(assets,name); await stat(file); } catch { file=legacy.get(name); }
        }
      }
      if (!file) {
        const response = await fetch('https://histree.wiki'+url.pathname+url.search);
        res.writeHead(response.status, {'Content-Type':response.headers.get('content-type')||'application/json'});
        res.end(Buffer.from(await response.arrayBuffer())); return;
      }
    } else {
      const candidate=resolve(dist,'.'+url.pathname);
      if (!candidate.startsWith(dist+'/')) file=resolve(dist,'index.html');
      else { try { if ((await stat(candidate)).isFile()) file=candidate; } catch { /* SPA route */ } }
      file ||= resolve(dist,'index.html');
    }
    res.writeHead(200,{'Content-Type':types[extname(file)]||'application/octet-stream'});
    res.end(await readFile(file));
  } catch (error) { res.writeHead(500).end(error.message); }
});
server.listen(48751,'127.0.0.1',()=>console.log('Story preview: http://127.0.0.1:48751'));
