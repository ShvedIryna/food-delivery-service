const BASE = '/api';
let token = localStorage.getItem('token');

export function setToken(value) {
  token = value;
  if (value) localStorage.setItem('token', value);
  else localStorage.removeItem('token');
}

export function getToken() {
  return token;
}

export async function api(path, { method = 'GET', body, params } = {}) {
  const headers = {};
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (token) headers.Authorization = `Bearer ${token}`;

  let url = BASE + path;
  if (params) {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== ''),
    ).toString();
    if (qs) url += `?${qs}`;
  }

  const res = await fetch(url, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    let message = `Помилка ${res.status}`;
    if (data?.detail) {
      message = typeof data.detail === 'string'
        ? data.detail
        : data.detail.map((d) => d.msg).join('; ');
    }
    const error = new Error(message);
    error.status = res.status;
    throw error;
  }
  return data;
}
