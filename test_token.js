async function run() {
  const token = 'sbp_7ab1bd0494fced69f43041cffa97a595578845f7';
  const response = await fetch('https://api.supabase.com/v1/projects', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  console.log(response.status);
}
run();
