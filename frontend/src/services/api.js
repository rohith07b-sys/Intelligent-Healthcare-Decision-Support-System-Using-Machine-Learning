const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5000/api").replace(/\/$/, "");


async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...options.headers,
      },
    });
  } catch {
    throw new Error("Cannot reach the API. Check that the Flask backend is running and the API URL is correct.");
  }
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(body.error || `Request failed (${response.status}).`);
    error.status = response.status;
    error.fieldErrors = body.field_errors || {};
    throw error;
  }
  return body;
}

export const api = {
  health: () => request("/health"),
  schema: () => request("/models/schema"),
  dashboard: () => request("/dashboard/stats"),
  assessments: (params) => request(`/assessments?${new URLSearchParams(params)}`),
  assessment: (id) => request(`/assessments/${id}`),
  createAssessment: (type, payload) => request(`/assessments/${type}`, {
    method: "POST",
    body: JSON.stringify(payload),
  }),
  performance: () => request("/models/performance"),
};
