const API_BASE =
  import.meta.env.VITE_MIGRATION_API_BASE_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = body?.detail || `HTTP ${response.status}`;
    throw new Error(String(detail));
  }
  return body;
}

export function getRuns() {
  return request("/approval/runs");
}

export function getRunDetails(runId) {
  return request(`/approval/runs/${encodeURIComponent(runId)}`);
}

export function submitDecision(runId, payload) {
  return request(`/approval/runs/${encodeURIComponent(runId)}/decision`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export { API_BASE };
