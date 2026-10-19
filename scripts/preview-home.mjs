import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { execFile } from 'node:child_process';

// Preview current UI against public content without editing local env files.
process.env.VITE_API_URL = '/api/v1';
process.env.VITE_ASK_API_URL = '/api/v1';
const require = createRequire(new URL('../apps/web/package.json', import.meta.url));
const { createServer } = await import(require.resolve('vite'));
const upstream = process.env.HISTREE_PREVIEW_API || 'https://histree.wiki';

// Native curl uses the macOS certificate store. Keep HTTPS verification enabled;
// Node may be unable to build the site's certificate chain on this workstation.
function publicApiProxy(request, response, next) {
  if (!request.url?.startsWith('/api/v1/')) return next();
  const args = ['--silent', '--show-error', '--max-time', '150', '--request', request.method,
    '--write-out', '\n%{http_code}', new URL(request.url, upstream).href];
  for (const name of ['content-type', 'x-histree-anonymous']) {
    if (request.headers[name]) args.push('--header', `${name}: ${request.headers[name]}`);
  }
  const hasBody = !['GET', 'HEAD'].includes(request.method);
  if (hasBody) args.push('--data-binary', '@-');
  const child = execFile('curl', args, { maxBuffer: 16 * 1024 * 1024 }, (error, stdout) => {
    if (response.destroyed) return;
    if (error) {
      response.writeHead(502, { 'Content-Type': 'application/json; charset=utf-8' });
      response.end(JSON.stringify({ message: '公开资料接口暂时无法连接，请稍后重试。' }));
      return;
    }
    const split = stdout.lastIndexOf('\n');
    const status = Number(stdout.slice(split + 1));
    const type = request.method === 'POST' && new URL(request.url, upstream).pathname === '/api/v1/ask'
      ? 'application/x-ndjson' : 'application/json';
    response.writeHead(status, { 'Content-Type': `${type}; charset=utf-8` });
    response.end(stdout.slice(0, split));
  });
  child.stdin.on('error', () => {});
  if (hasBody) request.pipe(child.stdin);
  else child.stdin.end();
  response.on('close', () => { if (!response.writableEnded) child.kill(); });
}
const server = await createServer({
  root: fileURLToPath(new URL('../apps/web', import.meta.url)),
  optimizeDeps: { include: ['@histree/shared-types'] },
  plugins: [{ name: 'home-preview-public-api', configureServer(server) { server.middlewares.use(publicApiProxy); } }],
  server: {
    host: '127.0.0.1',
    port: Number(process.env.PORT || 5187),
    strictPort: true,
  },
});
await server.listen();
server.printUrls();
