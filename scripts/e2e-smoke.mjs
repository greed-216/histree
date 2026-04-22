const WEB_URL = process.env.E2E_WEB_URL || 'http://localhost:5173/histree/';
const API_URL = process.env.E2E_API_URL || 'http://localhost:3000';

async function assertFetch(name, url, options, predicate) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5000);

  try {
    const response = await fetch(url, { ...options, signal: controller.signal });
    const body = await response.text();

    if (!predicate(response, body)) {
      throw new Error(`${name} failed: ${response.status} ${body.slice(0, 200)}`);
    }

    console.log(`ok - ${name}`);
  } finally {
    clearTimeout(timeout);
  }
}

await assertFetch('web app responds', WEB_URL, {}, (response, body) => {
  return response.ok && body.includes('<div id="root">');
});

await assertFetch('api health responds', `${API_URL}/`, {}, (response, body) => {
  return response.ok && body.includes('Hello World');
});

await assertFetch('admin people create rejects anonymous user', `${API_URL}/api/v1/people`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ name: 'Smoke Test Person' }),
}, (response) => response.status === 401);

await assertFetch('admin event create rejects anonymous user', `${API_URL}/api/v1/event`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ title: 'Smoke Test Event' }),
}, (response) => response.status === 401);
