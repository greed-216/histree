import OSS from 'ali-oss';
import Credential, { Config } from '@alicloud/credentials';
import { createHash } from 'node:crypto';
import type { Readable } from 'node:stream';

export const MAX_IMAGE_BYTES = 5 * 1024 * 1024;
export const IMAGE_CACHE_CONTROL = 'public, max-age=31536000, immutable';
const IMAGE_TYPES: Record<string, string> = {
  png: 'image/png',
  jpg: 'image/jpeg',
  webp: 'image/webp',
  gif: 'image/gif',
};

/** Only this explicitly public namespace is exposed by the website. */
export function imageKey(file: string): string {
  if (!/^[a-f0-9]{64}\.(png|jpg|webp|gif)$/.test(file))
    throw new Error('Invalid image name');
  return `public/images/${file}`;
}

export function imageType(file: string): string {
  imageKey(file);
  return IMAGE_TYPES[file.split('.').pop()!];
}

export function prepareImage(buffer: Buffer, declaredType?: string) {
  if (!buffer.length || buffer.length > MAX_IMAGE_BYTES)
    throw new Error('图片大小须为 1 字节至 5 MiB');
  let extension: string | undefined;
  if (
    buffer.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]))
  )
    extension = 'png';
  else if (buffer.subarray(0, 3).equals(Buffer.from([255, 216, 255])))
    extension = 'jpg';
  else if (
    ['GIF87a', 'GIF89a'].includes(buffer.subarray(0, 6).toString('ascii'))
  )
    extension = 'gif';
  else if (
    buffer.length >= 12 &&
    buffer.subarray(0, 4).toString('ascii') === 'RIFF' &&
    buffer.subarray(8, 12).toString('ascii') === 'WEBP'
  )
    extension = 'webp';
  if (!extension) throw new Error('仅支持 PNG、JPEG、WebP、GIF 图片');
  const contentType = IMAGE_TYPES[extension];
  if (declaredType && declaredType !== contentType)
    throw new Error('图片内容与声明类型不一致');
  const sha256 = createHash('sha256').update(buffer).digest('hex');
  const file = `${sha256}.${extension}`;
  return {
    file,
    key: imageKey(file),
    contentType,
    sha256,
    bytes: buffer.length,
    url: `/api/v1/media/images/${file}`,
  };
}

export function ossErrorCode(error: unknown): string {
  return typeof error === 'object' && error !== null && 'code' in error
    ? String(error.code)
    : 'StorageUnavailable';
}

/** The provider refreshes ECS STS credentials; no account key is needed on ECS. */
export class OssImages {
  private readonly credentials: Credential;
  private readonly bucket: string;
  private readonly region: string;
  private readonly endpoint: string;

  constructor(env: NodeJS.ProcessEnv = process.env) {
    this.bucket = env.HISTREE_OSS_BUCKET || '';
    if (!/^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$/.test(this.bucket))
      throw new Error('HISTREE_OSS_BUCKET is missing or invalid');
    this.region = env.HISTREE_OSS_REGION || 'oss-cn-beijing';
    if (!/^oss-[a-z0-9-]+$/.test(this.region))
      throw new Error('Invalid OSS region');
    this.endpoint =
      env.HISTREE_OSS_INTERNAL === 'true'
        ? `https://${this.region}-internal.aliyuncs.com`
        : `https://${this.region}.aliyuncs.com`;
    const type = env.HISTREE_OSS_CREDENTIAL_TYPE || 'ecs_ram_role';
    if (type === 'ecs_ram_role') {
      this.credentials = new Credential(
        new Config({
          type,
          roleName: env.HISTREE_OSS_ROLE_NAME,
          disableIMDSv1: true,
        }),
      );
    } else if (type === 'access_key' || type === 'sts') {
      if (
        !env.OSS_ACCESS_KEY_ID ||
        !env.OSS_ACCESS_KEY_SECRET ||
        (type === 'sts' && !env.OSS_SECURITY_TOKEN)
      )
        throw new Error('OSS credentials are incomplete');
      this.credentials = new Credential(
        new Config({
          type,
          accessKeyId: env.OSS_ACCESS_KEY_ID,
          accessKeySecret: env.OSS_ACCESS_KEY_SECRET,
          securityToken: env.OSS_SECURITY_TOKEN,
        }),
      );
    } else throw new Error('Unsupported OSS credential type');
  }

  private async client() {
    const { accessKeyId, accessKeySecret, securityToken } =
      await this.credentials.getCredential();
    if (!accessKeyId || !accessKeySecret)
      throw new Error('OSS credentials are unavailable');
    return new OSS({
      bucket: this.bucket,
      region: this.region,
      endpoint: this.endpoint,
      authorizationV4: true,
      accessKeyId,
      accessKeySecret,
      stsToken: securityToken,
      timeout: 15000,
    });
  }

  async upload(buffer: Buffer, declaredType?: string) {
    const image = prepareImage(buffer, declaredType);
    const client = await this.client();
    try {
      await client.put(image.key, buffer, {
        mime: image.contentType,
        headers: {
          'Cache-Control': IMAGE_CACHE_CONTROL,
          'x-oss-forbid-overwrite': 'true',
          'x-oss-meta-sha256': image.sha256,
        },
      });
    } catch (error) {
      if (ossErrorCode(error) !== 'FileAlreadyExists') throw error;
      const existing = await client.head(image.key);
      if (
        existing.meta?.sha256 !== image.sha256 ||
        Number(
          (existing.res.headers as Record<string, string>)['content-length'],
        ) !== image.bytes
      )
        throw new Error('Existing object does not match image');
    }
    return image;
  }

  async read(file: string) {
    const key = imageKey(file);
    const result = await (await this.client()).getStream(key);
    return { stream: result.stream as Readable, res: result.res };
  }
}
