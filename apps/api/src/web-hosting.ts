import { existsSync } from 'node:fs';
import { resolve } from 'node:path';
import type { NestExpressApplication } from '@nestjs/platform-express';
import type { Request, Response, NextFunction } from 'express';

export function configureWebHosting(app: NestExpressApplication, webRoot: string) {
  const root = resolve(webRoot);
  const index = resolve(root, 'index.html');
  if (!existsSync(index)) throw new Error(`Frontend build missing: ${index}`);
  app.useStaticAssets(root, {
    index: false,
    setHeaders(res, file) {
      res.setHeader('Cache-Control', file.startsWith(resolve(root, 'assets') + '/')
        ? 'public, max-age=31536000, immutable' : 'no-cache');
    },
  });
  // Browser routes receive the app shell; missing assets and API routes keep real 404s.
  app.use((req: Request, res: Response, next: NextFunction) => {
    if (!['GET', 'HEAD'].includes(req.method) || /^\/api(?:\/|$)/i.test(req.path)
      || req.path.split('/').some(part => part.includes('.')) || !req.accepts('html')) return next();
    res.setHeader('Cache-Control', 'no-cache');
    res.sendFile(index);
  });
}
