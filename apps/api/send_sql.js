const fs = require('fs');

async function run() {
  // Let's use the management API endpoint for SQL execution correctly
  // Wait, Supabase CLI does this via `/v1/projects/${ref}/database/query` instead of `/pg/query`.
  const token = 'sbp_7ab1bd0494fced69f43041cffa97a595578845f7';
  const projectRef = 'ilnwjhabcqtxkkuhddyt';
  
  const schemaSql = fs.readFileSync('../../supabase/migrations/20260414130000_v2_schema.sql', 'utf8');
  const rlsSql = fs.readFileSync('../../supabase/migrations/20260414140000_rls_and_roles.sql', 'utf8');
  const grantAdminSql = `INSERT INTO public.user_roles (user_id, role) VALUES ('b8b84207-312f-4bed-b2a1-3391e7e6b51a', 'admin') ON CONFLICT (user_id) DO UPDATE SET role = 'admin';`;

  const fullSql = `
    ${schemaSql}
    ${rlsSql}
    ${grantAdminSql}
  `;

  try {
    const response = await fetch(`https://api.supabase.com/v1/projects/${projectRef}/database/query`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ query: fullSql })
    });

    const result = await response.json();

    if (!response.ok) {
      console.error('Failed to execute SQL:', JSON.stringify(result, null, 2));
    } else {
      console.log('SQL executed successfully via HTTPS Management API!');
    }
  } catch (err) {
    console.error('Fetch error:', err.message);
  }
}
run();
