import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { Controller, Get } from '@nestjs/common';
import { Test } from '@nestjs/testing';
import type { NestExpressApplication } from '@nestjs/platform-express';
import request from 'supertest';
import { configureWebHosting } from './web-hosting';

@Controller('api/v1')
class FixtureController {
  @Get('status') status() { return { available: true }; }
}

describe('combined frontend and API hosting', () => {
  let app: NestExpressApplication;
  let root: string;
  beforeAll(async () => {
    root = mkdtempSync(join(tmpdir(), 'histree-web-'));
    mkdirSync(join(root, 'assets'));
    writeFileSync(join(root, 'index.html'), '<html><div id="root"></div></html>');
    writeFileSync(join(root, 'assets', 'app-123.js'), 'window.fixture = true;');
    const module = await Test.createTestingModule({ controllers: [FixtureController] }).compile();
    app = module.createNestApplication<NestExpressApplication>();
    configureWebHosting(app, root);
    await app.init();
  });
  afterAll(async () => { await app.close(); rmSync(root, { recursive: true, force: true }); });
  it('serves the shell for root and direct browser routes without caching it', async () => {
    for (const route of ['/', '/people/example?source=link', '/ask']) {
      await request(app.getHttpServer()).get(route).expect(200).expect('Cache-Control', 'no-cache').expect(/id="root"/);
    }
    await request(app.getHttpServer()).head('/ask').expect(200);
  });
  it('caches hashed assets and keeps missing assets and API routes as 404s', async () => {
    await request(app.getHttpServer()).get('/assets/app-123.js').expect(200)
      .expect('Cache-Control', 'public, max-age=31536000, immutable');
    await request(app.getHttpServer()).get('/assets/missing.js').expect(404);
    await request(app.getHttpServer()).get('/api/v1/missing').expect(404);
    await request(app.getHttpServer()).get('/API/V1/missing').expect(404);
    await request(app.getHttpServer()).post('/ask').expect(404);
    await request(app.getHttpServer()).get('/api/v1/status').expect(200, { available: true });
    await request(app.getHttpServer()).get('/API/V1/status').expect(200, { available: true });
  });
  it('refuses to start when the frontend build is missing', () => {
    expect(() => configureWebHosting(app, join(root, 'absent'))).toThrow('Frontend build missing');
  });
});
