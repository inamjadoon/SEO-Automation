const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// Customer endpoints
export const customerApi = {
  submitSite: (siteId, domain) =>
    request("/api/sites/register", {
      method: "POST",
      body: JSON.stringify({ site_id: siteId, domain }),
    }),

  getSnippet: (siteId) => request(`/api/sites/${siteId}/snippet`),
  getJsonLdStatus: (siteId) => request(`/api/sites/${siteId}/jsonld-status`),
};

// Admin endpoints
export const adminApi = {
  getAllSites: () => request("/api/admin/sites"),
  getSyncStatus: (siteId) => request(`/api/admin/sites/${siteId}/sync`),
  triggerSync: (siteId) =>
    request(`/api/admin/sites/${siteId}/sync`, { method: "POST" }),
  triggerAllSync: () =>
    request("/api/admin/sync-all", { method: "POST" }),
};
