import React, { useState } from "react";
import { Button, Input, Alert } from "../ui/index.jsx";
import { customerApi } from "../../services/api.js";

export function SiteRegistrationForm({ onSuccess }) {
  const [siteId, setSiteId] = useState("");
  const [domain, setDomain] = useState("");
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState(null);

  function validate() {
    const e = {};
    if (!siteId.trim()) e.siteId = "Site ID is required";
    if (!domain.trim()) e.domain = "Domain is required";
    else if (!/^[a-zA-Z0-9][a-zA-Z0-9-_.]+\.[a-zA-Z]{2,}$/.test(domain.trim()))
      e.domain = "Enter a valid domain (e.g. mysite.com)";
    return e;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const v = validate();
    if (Object.keys(v).length) return setErrors(v);
    setErrors({});
    setApiError(null);
    setLoading(true);
    try {
      const result = await customerApi.submitSite(siteId.trim(), domain.trim());
      onSuccess?.(result);
    } catch (err) {
      setApiError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="reg-form" onSubmit={handleSubmit} noValidate>
      <div className="reg-form-fields">
        <Input
          label="Site ID"
          placeholder="e.g. sq-a1b2c3d4"
          value={siteId}
          onChange={(e) => setSiteId(e.target.value)}
          error={errors.siteId}
          hint="Your unique Squarespace site identifier"
          autoComplete="off"
        />
        <Input
          label="Domain"
          placeholder="e.g. mybusiness.com"
          value={domain}
          onChange={(e) => setDomain(e.target.value)}
          error={errors.domain}
          hint="Primary domain without https://"
          autoComplete="off"
        />
      </div>

      {apiError && (
        <Alert type="error" title="Submission failed">
          {apiError}
        </Alert>
      )}

      <Button type="submit" loading={loading} className="reg-submit">
        {loading ? "Connecting…" : "Generate SEO Snippet →"}
      </Button>
    </form>
  );
}
