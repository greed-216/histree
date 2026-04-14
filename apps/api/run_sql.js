const { Client } = require('pg');
const fs = require('fs');

const encodedPassword = encodeURIComponent('+gs1000wBtxhsjhy');
const connectionString = `postgresql://postgres:${encodedPassword}@db.ilnwjhabcqtxkkuhddyt.supabase.co:5432/postgres`;

const client = new Client({
  connectionString,
  ssl: { rejectUnauthorized: false }
});

async function run() {
  try {
    console.log('Connecting to database...');
    await client.connect();
    console.log('Connected. Reading SQL files...');
    
    // Run schema
    const schemaSql = fs.readFileSync('../../supabase/migrations/20260414130000_v2_schema.sql', 'utf8');
    await client.query(schemaSql);
    console.log('v2_schema executed successfully!');
    
    // Run RLS
    const rlsSql = fs.readFileSync('../../supabase/migrations/20260414140000_rls_and_roles.sql', 'utf8');
    await client.query(rlsSql);
    console.log('rls_and_roles executed successfully!');
    
    // Give user admin access
    const adminSql = `INSERT INTO public.user_roles (user_id, role) VALUES ('b8b84207-312f-4bed-b2a1-3391e7e6b51a', 'admin') ON CONFLICT DO NOTHING;`;
    await client.query(adminSql);
    console.log('Granted admin role to your user!');
    
  } catch (err) {
    console.error('Error executing migration:', err);
  } finally {
    await client.end();
  }
}

run();
