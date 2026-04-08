import React, { useCallback, useEffect, useState } from "react";
import { SitesTable } from "../components/admin/SitesTable.jsx";
import { StatsBar } from "../components/admin/StatsBar.jsx";
import { SectionHeader, Button, Alert } from "../components/ui/index.jsx";
import { adminApi } from "../services/api.js";
import { useAsync } from "../hooks/useAsync.js";

export function AdminPage() {
  const [sites, setSites] = useState([]);
  const [syncAllMsg, setSyncAllMsg] = useState(null);

  const { loading, error, execute: fetchSites } = useAsync(
    useCallback(async () => {
      const data = await adminApi.getAllSites();
      setSites(data?.sites || data || []);
      return data;
    }, [])
  );

  const { loading: syncingAll, execute: runSyncAll } = useAsync(adminApi.triggerAllSync);

  useEffect(() => { fetchSites(); }, []);

  async function handleSyncAll() {
    setSyncAllMsg(null);
    try {
      await runSyncAll();
      setSyncAllMsg({ type: "success", text: "Sync triggered for all sites." });
      setTimeout(() => fetchSites(), 1500);
    } catch (e) {
      setSyncAllMsg({ type: "error", text: e.message });
    }
  }

  return (
    <div className="admin-page">
      <SectionHeader
        title="Admin Dashboard"
        subtitle="Monitor all registered sites, sync status, and JSON-LD health"
        action={
          <div className="admin-actions">
            <Button variant="secondary" onClick={fetchSites} loading={loading}>
              ↺ Refresh
            </Button>
            <Button onClick={handleSyncAll} loading={syncingAll}>
              Sync All Sites
            </Button>
          </div>
        }
      />

      {syncAllMsg && (
        <Alert type={syncAllMsg.type}>
          {syncAllMsg.text}
        </Alert>
      )}

      <StatsBar sites={sites} />

      <div className="admin-table-section">
        <SitesTable
          sites={sites}
          loading={loading}
          error={error}
          onRefresh={fetchSites}
        />
      </div>
    </div>
  );
}
