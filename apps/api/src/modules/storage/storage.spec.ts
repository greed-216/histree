import { Readable } from 'node:stream';
import type { Server } from 'node:http';
import { createHash } from 'node:crypto';
import { Test } from '@nestjs/testing';
import type { INestApplication } from '@nestjs/common';
import request from 'supertest';
import OSS from 'ali-oss';
import Credential from '@alicloud/credentials';
import {
  OssImages,
  MAX_IMAGE_BYTES,
  imageKey,
  prepareImage,
} from './oss-images';
import { StorageModule } from './storage.module';

jest.mock('ali-oss');
jest.mock('@alicloud/credentials', () => ({
  __esModule: true,
  default: jest.fn(),
  Config: class {
    constructor(values: object) {
      Object.assign(this, values);
    }
  },
}));

// A complete 1x1 PNG, independent of filename or multipart MIME declarations.
const png = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=',
  'base64',
);
const image = prepareImage(png);

describe('OSS image boundaries', () => {
  let put: jest.Mock,
    head: jest.Mock,
    getStream: jest.Mock,
    getCredential: jest.Mock;
  beforeEach(() => {
    jest.clearAllMocks();
    put = jest.fn().mockResolvedValue({});
    head = jest.fn().mockResolvedValue({
      meta: { sha256: image.sha256 },
      res: { headers: { 'content-length': String(png.length) } },
    });
    getStream = jest.fn().mockImplementation(() =>
      Promise.resolve({
        stream: Readable.from(png),
        res: { headers: { 'content-length': String(png.length) } },
      }),
    );
    getCredential = jest.fn().mockResolvedValue({
      accessKeyId: 'temporary-id',
      accessKeySecret: 'temporary-secret',
      securityToken: 'temporary-token',
    });
    (Credential as jest.Mock).mockImplementation(() => ({ getCredential }));
    (OSS as unknown as jest.Mock).mockImplementation(() => ({
      put,
      head,
      getStream,
    }));
  });

  it('uses the actual image format and content hash, rejects SVG, MIME spoofing and size violations', () => {
    expect(image.sha256).toBe(createHash('sha256').update(png).digest('hex'));
    expect(image.key).toBe(`public/images/${image.sha256}.png`);
    for (const body of [
      Buffer.alloc(0),
      Buffer.alloc(MAX_IMAGE_BYTES + 1),
      Buffer.from('<svg onload="alert(1)"></svg>'),
    ])
      expect(() => prepareImage(body)).toThrow();
    expect(() => prepareImage(png, 'image/jpeg')).toThrow();
    for (const file of [
      '../private.jpg',
      'private/key.png',
      `${image.sha256}.svg`,
      `${image.sha256}.png?x=1`,
    ])
      expect(() => imageKey(file)).toThrow();
  });

  it('uses V4 and refreshed STS credentials over the same-region private endpoint', async () => {
    const store = new OssImages({
      HISTREE_OSS_BUCKET: 'histree',
      HISTREE_OSS_INTERNAL: 'true',
    });
    await expect(store.upload(png, 'image/png')).resolves.toEqual(image);
    getCredential.mockResolvedValue({
      accessKeyId: 'rotated-id',
      accessKeySecret: 'rotated-secret',
      securityToken: 'rotated-token',
    });
    await store.read(image.file);
    expect(OSS).toHaveBeenLastCalledWith(
      expect.objectContaining({
        authorizationV4: true,
        endpoint: 'https://oss-cn-beijing-internal.aliyuncs.com',
        accessKeyId: 'rotated-id',
        stsToken: 'rotated-token',
      }),
    );
    expect(put).toHaveBeenCalledWith(
      image.key,
      png,
      expect.objectContaining({
        headers: expect.objectContaining({
          'x-oss-forbid-overwrite': 'true',
        }) as unknown,
      }),
    );
  });

  it('allows idempotent uploads only when the existing metadata and size match', async () => {
    const store = new OssImages({ HISTREE_OSS_BUCKET: 'histree' });
    put.mockRejectedValue({ code: 'FileAlreadyExists' });
    await expect(store.upload(png)).resolves.toEqual(image);
    head.mockResolvedValue({
      meta: { sha256: 'different' },
      res: { headers: { 'content-length': String(png.length) } },
    });
    await expect(store.upload(png)).rejects.toThrow('does not match');
  });

  it('does not initialize missing or partial credentials', () => {
    expect(() => new OssImages({})).toThrow('HISTREE_OSS_BUCKET');
    expect(
      () =>
        new OssImages({
          HISTREE_OSS_BUCKET: 'histree',
          HISTREE_OSS_CREDENTIAL_TYPE: 'sts',
          OSS_ACCESS_KEY_ID: 'id',
          OSS_ACCESS_KEY_SECRET: 'secret',
        }),
    ).toThrow('incomplete');
  });

  describe('public HTTP reads', () => {
    let app: INestApplication<Server>;
    const previousBucket = process.env.HISTREE_OSS_BUCKET;
    beforeEach(async () => {
      process.env.HISTREE_OSS_BUCKET = 'histree';
      const module = await Test.createTestingModule({
        imports: [StorageModule],
      }).compile();
      app = module.createNestApplication();
      await app.init();
    });
    afterEach(async () => {
      await app.close();
      if (previousBucket === undefined) delete process.env.HISTREE_OSS_BUCKET;
      else process.env.HISTREE_OSS_BUCKET = previousBucket;
    });

    it('serves exact bytes under a stable cacheable URL and keeps writes unavailable', async () => {
      const response = await request(app.getHttpServer())
        .get(image.url)
        .expect(200)
        .expect('Content-Type', 'image/png')
        .expect('X-Content-Type-Options', 'nosniff');
      expect(response.body).toEqual(png);
      expect(response.headers['cache-control']).toContain('immutable');
      await request(app.getHttpServer()).post('/api/v1/upload').expect(404);
      await request(app.getHttpServer())
        .get('/api/v1/media/images/private.svg')
        .expect(404);
      expect(getStream).toHaveBeenCalledTimes(1);
    });

    it('returns 404 for missing objects and hides SDK details on storage outages', async () => {
      getStream.mockRejectedValueOnce({ code: 'NoSuchKey' });
      await request(app.getHttpServer()).get(image.url).expect(404);
      getStream.mockRejectedValueOnce({
        code: 'AccessDenied',
        message: 'private-secret-signature',
      });
      const failure = await request(app.getHttpServer())
        .get(image.url)
        .expect(503);
      expect(JSON.stringify(failure.body)).not.toContain('private-secret');
      expect(failure.headers['cache-control'] || '').not.toContain('immutable');
    });
  });
});
