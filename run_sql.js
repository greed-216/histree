const { Client } = require('pg');
const fs = require('fs');

const client = new Client({
  connectionString: 'postgresql://postgres:+gs1000wBtxhsjhy@db.ilnwjhabcqtxkkuhddyt.supabase.co:5432/postgres'
});

async function run() {
  try {
    await client.connect();
    const sql = fs.readFileSync('supabase/migrations/20260414130000_v2_schema.sql', 'utf8');
    await client.query(sql);
    console.log('Migration executed successfully!');
  } catch (err) {
    console.error('Error executing migration:', err);
  } finally {
    await client.end();
  }
}

run();
