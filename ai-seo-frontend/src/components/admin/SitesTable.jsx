import React from "react";
import { Badge, Button, StatusDot, Spinner } from "../ui/index.jsx";
import { adminApi } from "../../services/api.js";
import { useAsync } from "../../hooks/useAsync.js";

function SyncButton({ siteId, onDone }) {
  const { loading, execute } = useAsync(() => adminApi.triggerSync(siteId));

  async function handleSync() {
    try {
      await execute();
      onDone?.();
    } catch (_) {}
  }

  return (
    <Button variant="ghost" loading={loading} onClick={handleSync} className="sync-btn">
      {loading ? "" : "↺ Sync"}
    </Button>
  );
}

function statusVariant(s) {
  return { synced: "success", syncing: "warning", error: "error", pending: "neutral" }[s] || "neutral";
}

export function SitesTable({ sites, loading, error, onRefresh }) {
  if (loading)
    return (
      <div className="table-state">
        <Spinner size="lg" />
        <span>Loading sites…</span>
      </div>
    );

  if (error)
    return (
      <div className="table-state table-state--error">
        <span>⚠ {error}</span>
        <Button variant="secondary" onClick={onRefresh}>Retry</Button>
      </div>
    );

  if (!sites?.length)
    return (
      <div className="table-state table-state--empty">
        <span className="empty-icon">◎</span>
        <span>No sites registered yet</span>
      </div>
    );

  return (
    <div className="table-wrap">
      <table className="sites-table">
        <thead>
          <tr>
            <th>Site ID</th>
            <th>Domain</th>
            <th>Status</th>
            <th>Last Synced</th>
            <th>JSON-LD</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {sites.map((site) => (
            <tr key={site.site_id} className="sites-row">
              <td>
                <code className="site-id-cell">{site.site_id}</code>
              </td>
              <td>
                <a
                  href={`https://${site.domain}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="domain-link"
                >
                  {site.domain}
                </a>
              </td>
              <td>
                <div className="status-cell">
                  <StatusDot status={statusVariant(site.sync_status)} />
                  <Badge status={statusVariant(site.sync_status)}>
                    {site.sync_status || "unknown"}
                  </Badge>
                </div>
              </td>
              <td className="timestamp-cell">
                {site.last_synced
                  ? new Date(site.last_synced).toLocaleString()
                  : "—"}
              </td>
              <td>
                <Badge status={site.jsonld_active ? "success" : "neutral"}>
                  {site.jsonld_active ? "Active" : "Inactive"}
                </Badge>
              </td>
              <td>
                <SyncButton siteId={site.site_id} onDone={onRefresh} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
