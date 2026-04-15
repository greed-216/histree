const fs = require('fs');

async function run() {
  const token = 'sbp_7ab1bd0494fced69f43041cffa97a595578845f7';
  const projectRef = 'ilnwjhabcqtxkkuhddyt';
  
  const sql = fs.readFileSync('../../supabase/migrations/20260414150000_add_images_and_locations.sql', 'utf8');

  try {
    const response = await fetch(`https://api.supabase.com/v1/projects/${projectRef}/database/query`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ query: sql })
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
