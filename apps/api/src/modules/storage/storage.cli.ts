import { open } from 'node:fs/promises';
import {
  MAX_IMAGE_BYTES,
  OssImages,
  ossErrorCode,
  prepareImage,
} from './oss-images';

async function main() {
  const [command, path, ...extra] = process.argv.slice(2);
  if (!['check', 'upload'].includes(command) || !path || extra.length)
    throw new Error(
      'Usage: node dist/modules/storage/storage.cli.js <check|upload> <image-file>',
    );
  const handle = await open(path, 'r');
  let buffer: Buffer;
  try {
    const stat = await handle.stat();
    if (!stat.isFile() || stat.size < 1 || stat.size > MAX_IMAGE_BYTES)
      throw new Error('Expected an image file of 1 byte to 5 MiB');
    buffer = await handle.readFile();
  } finally {
    await handle.close();
  }
  const result =
    command === 'check'
      ? prepareImage(buffer)
      : await new OssImages().upload(buffer);
  console.log(
    JSON.stringify({ ...result, uploaded: command === 'upload' }, null, 2),
  );
}

main().catch((error: unknown) => {
  const code = ossErrorCode(error);
  console.error(
    code !== 'StorageUnavailable'
      ? `OSS operation failed (${code})`
      : error instanceof Error
        ? error.message
        : 'Storage operation failed',
  );
  process.exitCode = 1;
});
