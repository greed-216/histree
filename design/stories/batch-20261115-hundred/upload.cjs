// Run only inside the existing production container, against this batch's public assets.
const fs = require('node:fs/promises');
const path = require('node:path');
const { createHash } = require('node:crypto');
const { OssImages } = require('/app/apps/api/dist/modules/storage/oss-images.js');
async function main() {
  const dir = process.argv[2];
  const manifest = JSON.parse(await fs.readFile(path.join(dir, 'assets.json'), 'utf8'));
  const oss = new OssImages();
  const results = [];
  for (let offset = 0; offset < manifest.length; offset += 3) {
    const batch = await Promise.all(manifest.slice(offset, offset + 3).map(async item => {
      if (!/^[a-f0-9]{64}\.(png|webp)$/.test(item.file)) throw new Error('Invalid public image filename');
      const bytes = await fs.readFile(path.join(dir, item.file));
      if (bytes.length !== item.bytes || createHash('sha256').update(bytes).digest('hex') !== item.sha256) throw new Error('Batch asset hash mismatch');
      const result = await oss.upload(bytes);
      if (result.sha256 !== item.sha256 || result.bytes !== item.bytes) throw new Error('Upload returned different metadata');
      return result;
    }));
    results.push(...batch);
  }
  process.stdout.write(JSON.stringify(results));
}
main().catch(error => { console.error(error.message); process.exitCode = 1; });
