

const API_BASE = (import.meta.env.VITE_API_URL || '/api/v1').replace(/\/$/, '');

type ApiOptions = RequestInit;

export async function apiFetch<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const { headers, ...requestInit } = options;

  const requestHeaders = new Headers(headers);
  const response = await fetch(`${API_BASE}${path}`, {
    ...requestInit,
    headers: requestHeaders,
  });

  if (!response.ok) {
    const body = await response.text();
    let message = body;
    try { const parsed = JSON.parse(body); message = Array.isArray(parsed.message) ? parsed.message.join('；') : parsed.message || body; } catch { /* Response may be plain text. */ }
    throw new Error(message || `请求失败（${response.status}）`);
  }

  return response.json() as Promise<T>;
}
