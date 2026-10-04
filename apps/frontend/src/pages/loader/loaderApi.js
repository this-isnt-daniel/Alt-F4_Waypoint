const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

async function request(path, { token, method = 'GET', body } = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...(body ? { body: JSON.stringify(body) } : {}),
  });

  const text = await response.text();
  const data = text ? JSON.parse(text) : null;
  if (!response.ok) {
    const detail = data?.detail;
    const message = Array.isArray(detail)
      ? detail.map((item) => item.msg).join(', ')
      : detail || `Request failed with ${response.status}`;
    throw new Error(message);
  }
  return data;
}

export async function loginLoader(username, password) {
  return request('/auth/login', {
    method: 'POST',
    body: { username, password },
  });
}

export async function fetchLoaderProfile(token) {
  return request('/auth/me', { token });
}

export async function fetchLoaderQueue(token) {
  return request('/loader/queue', { token });
}

export async function fetchLoaderWorkbench(token, tripId) {
  return request(`/loader/trips/${encodeURIComponent(tripId)}/workbench`, { token });
}

export async function startLoading(token, tripId) {
  return request(`/loader/trips/${encodeURIComponent(tripId)}/start`, {
    token,
    method: 'POST',
  });
}

export async function saveLoadItem(token, tripId, lineItemId, body) {
  return request(`/loader/trips/${encodeURIComponent(tripId)}/items/${encodeURIComponent(lineItemId)}`, {
    token,
    method: 'PATCH',
    body,
  });
}

export async function completeStop(token, tripId, stopId) {
  return request(`/loader/trips/${encodeURIComponent(tripId)}/complete-stop/${encodeURIComponent(stopId)}`, {
    token,
    method: 'POST',
  });
}

export async function submitLoad(token, tripId, body) {
  return request(`/loader/trips/${encodeURIComponent(tripId)}/load`, {
    token,
    method: 'POST',
    body,
  });
}

export async function markVehicleUnavailable(token, tripId, body) {
  return request(`/loader/trips/${encodeURIComponent(tripId)}/vehicle-unavailable`, {
    token,
    method: 'POST',
    body,
  });
}

export async function fetchLoaderDeferrals(token) {
  return request('/loader/deferrals', { token });
}
