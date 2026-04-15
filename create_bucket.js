const { createClient } = require('@supabase/supabase-js');
const supabase = createClient(
  'https://ilnwjhabcqtxkkuhddyt.supabase.co',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlsbndqaGFiY3F0eGtrdWhkZHl0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjE1OTg2MCwiZXhwIjoyMDkxNzM1ODYwfQ.4C6geUTqnQ3Uj8NOxUDhNJHTnRFB80iLMsC4RW604cY'
);
async function run() {
  const { data, error } = await supabase.storage.createBucket('images', { public: true });
  console.log('Create Bucket:', data, error);
}
run();
