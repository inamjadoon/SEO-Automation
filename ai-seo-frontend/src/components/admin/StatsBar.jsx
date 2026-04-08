import React from "react";

function Stat({ label, value, accent }) {
  return (
    <div className={`stat-card ${accent ? `stat-card--${accent}` : ""}`}>
      <div className="stat-value">{value ?? "—"}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}

export function StatsBar({ sites = [] }) {
  const total = sites.length;
  const synced = sites.filter((s) => s.sync_status === "synced").length;
  const errors = sites.filter((s) => s.sync_status === "error").length;
  const pending = sites.filter((s) => s.sync_status === "pending").length;
  const jsonldActive = sites.filter((s) => s.jsonld_active).length;

  return (
    <div className="stats-bar">
      <Stat label="Total Sites" value={total} />
      <Stat label="Synced" value={synced} accent="green" />
      <Stat label="Pending" value={pending} accent="yellow" />
      <Stat label="Errors" value={errors} accent="red" />
      <Stat label="JSON-LD Active" value={jsonldActive} accent="blue" />
    </div>
  );
}
