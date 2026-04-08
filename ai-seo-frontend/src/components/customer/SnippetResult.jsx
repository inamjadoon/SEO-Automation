import React, { useEffect, useState } from "react";
import { Card, CodeBlock, Badge, Alert, Button, Spinner } from "../ui/index.jsx";
import { customerApi } from "../../services/api.js";

function JsonLdStatus({ siteId }) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    customerApi
      .getJsonLdStatus(siteId)
      .then(setStatus)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [siteId]);

  if (loading) return <Spinner size="sm" />;
  if (error) return <Badge status="error">Status unavailable</Badge>;

  const s = status?.status || "unknown";
  const statusMap = {
    active: "success",
    pending: "warning",
    error: "error",
    unknown: "neutral",
  };

  return (
    <div className="jsonld-status">
      <Badge status={statusMap[s] || "neutral"}>
        JSON-LD: {s.charAt(0).toUpperCase() + s.slice(1)}
      </Badge>
      {status?.last_synced && (
        <span className="last-sync">
          Last synced {new Date(status.last_synced).toLocaleString()}
        </span>
      )}
    </div>
  );
}

export function SnippetResult({ result, onReset }) {
  const { site_id, domain, snippet } = result;
  const [snippetData, setSnippetData] = useState(snippet || null);
  const [loadingSnippet, setLoadingSnippet] = useState(!snippet);
  const [snippetError, setSnippetError] = useState(null);

  useEffect(() => {
    if (snippet) return;
    customerApi
      .getSnippet(site_id)
      .then((d) => setSnippetData(d?.snippet || d))
      .catch((e) => setSnippetError(e.message))
      .finally(() => setLoadingSnippet(false));
  }, [site_id, snippet]);

  const snippetCode =
    typeof snippetData === "string"
      ? snippetData
      : snippetData?.code || "<!-- Snippet not available -->";

  return (
    <div className="snippet-result">
      <div className="result-header">
        <div className="result-meta">
          <div className="result-site">
            <span className="result-domain">{domain}</span>
            <span className="result-id">#{site_id}</span>
          </div>
          <JsonLdStatus siteId={site_id} />
        </div>
        <Button variant="ghost" onClick={onReset} className="result-reset">
          ← Register another
        </Button>
      </div>

      <Card accent="green" className="result-card">
        <div className="result-card-label">
          <span className="label-dot" />
          Squarespace Code Injection Snippet
        </div>

        {loadingSnippet ? (
          <div className="snippet-loading">
            <Spinner />
            <span>Generating snippet…</span>
          </div>
        ) : snippetError ? (
          <Alert type="error" title="Could not load snippet">
            {snippetError}
          </Alert>
        ) : (
          <CodeBlock code={snippetCode} language="html" />
        )}
      </Card>

      <Card className="result-instructions">
        <h3 className="instructions-title">How to install</h3>
        <ol className="instructions-list">
          <li>Open your Squarespace Dashboard → <strong>Settings</strong></li>
          <li>Navigate to <strong>Advanced → Code Injection</strong></li>
          <li>Paste the snippet above into the <strong>Header</strong> section</li>
          <li>Click <strong>Save</strong> — your AI SEO layer is now active</li>
        </ol>
      </Card>
    </div>
  );
}
