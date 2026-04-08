import React, { useState } from "react";
import { SiteRegistrationForm } from "../components/customer/SiteRegistrationForm.jsx";
import { SnippetResult } from "../components/customer/SnippetResult.jsx";

export function CustomerPage() {
  const [result, setResult] = useState(null);

  return (
    <div className="customer-page">
      <div className="customer-hero">
        <div className="hero-badge">AI SEO System</div>
        <h1 className="hero-title">
          Connect your Squarespace<br />
          <em>to intelligent SEO</em>
        </h1>
        <p className="hero-subtitle">
          Enter your site details below to generate a custom code snippet and
          activate AI-powered structured data on your site.
        </p>
      </div>

      <div className="customer-body">
        {!result ? (
          <div className="form-container">
            <div className="form-card">
              <h2 className="form-card-title">Register your site</h2>
              <SiteRegistrationForm onSuccess={setResult} />
            </div>
          </div>
        ) : (
          <SnippetResult result={result} onReset={() => setResult(null)} />
        )}
      </div>
    </div>
  );
}
