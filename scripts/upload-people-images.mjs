import { readFileSync } from 'node:fs';
import { basename } from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(new URL('../apps/api/package.json', import.meta.url));
const { createClient } = require('@supabase/supabase-js');

function loadEnv(path) {
  const env = {};
  const raw = readFileSync(path, 'utf8');

  for (const line of raw.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const index = trimmed.indexOf('=');
    if (index === -1) continue;
    env[trimmed.slice(0, index)] = trimmed.slice(index + 1);
  }

  return env;
}

const env = {
  ...loadEnv('apps/api/.env'),
  ...process.env,
};

const supabaseUrl = env.SUPABASE_URL;
const serviceRoleKey = env.SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseUrl || !serviceRoleKey) {
  throw new Error('Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY.');
}

const supabase = createClient(supabaseUrl, serviceRoleKey, {
  auth: { persistSession: false },
});

const manifest = JSON.parse(readFileSync('resources/people/manifest.json', 'utf8'));
const bucket = 'images';

const { data: buckets, error: bucketListError } = await supabase.storage.listBuckets();
if (bucketListError) throw bucketListError;

if (!buckets.some((item) => item.name === bucket)) {
  const { error: createBucketError } = await supabase.storage.createBucket(bucket, { public: true });
  if (createBucketError) throw createBucketError;
  console.log(`created storage bucket: ${bucket}`);
}

for (const item of manifest) {
  const filePath = item.image;
  const objectPath = `people/${basename(filePath)}`;
  const fileBuffer = readFileSync(filePath);

  const { error: uploadError } = await supabase.storage
    .from(bucket)
    .upload(objectPath, fileBuffer, {
      contentType: 'image/png',
      upsert: true,
    });

  if (uploadError) throw new Error(`${item.name}: ${uploadError.message}`);

  const { data: publicUrlData } = supabase.storage.from(bucket).getPublicUrl(objectPath);
  const { error: updateError } = await supabase
    .from('person')
    .update({ image_url: publicUrlData.publicUrl })
    .eq('id', item.id);

  if (updateError) throw new Error(`${item.name}: ${updateError.message}`);

  console.log(`uploaded ${item.name} -> ${objectPath}`);
}
