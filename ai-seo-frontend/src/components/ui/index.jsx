import React from "react";

// ── Button ──────────────────────────────────────────────────────────────────
export function Button({ children, variant = "primary", loading, className = "", ...props }) {
  const variants = {
    primary: "btn-primary",
    secondary: "btn-secondary",
    danger: "btn-danger",
    ghost: "btn-ghost",
  };
  return (
    <button
      className={`btn ${variants[variant]} ${loading ? "btn-loading" : ""} ${className}`}
      disabled={loading || props.disabled}
      {...props}
    >
      {loading ? <span className="spinner" /> : null}
      {children}
    </button>
  );
}

// ── Input ───────────────────────────────────────────────────────────────────
export function Input({ label, error, hint, className = "", ...props }) {
  return (
    <div className={`field ${className}`}>
      {label && <label className="field-label">{label}</label>}
      <input className={`field-input ${error ? "field-input--error" : ""}`} {...props} />
      {hint && !error && <span className="field-hint">{hint}</span>}
      {error && <span className="field-error">{error}</span>}
    </div>
  );
}

// ── Card ─────────────────────────────────────────────────────────────────────
export function Card({ children, className = "", accent }) {
  return (
    <div className={`card ${accent ? `card--${accent}` : ""} ${className}`}>
      {children}
    </div>
  );
}

// ── Badge ─────────────────────────────────────────────────────────────────────
export function Badge({ children, status = "neutral" }) {
  return <span className={`badge badge--${status}`}>{children}</span>;
}

// ── Alert ─────────────────────────────────────────────────────────────────────
export function Alert({ type = "info", title, children }) {
  const icons = { info: "ℹ", success: "✓", warning: "⚠", error: "✕" };
  return (
    <div className={`alert alert--${type}`}>
      <span className="alert-icon">{icons[type]}</span>
      <div>
        {title && <strong className="alert-title">{title}</strong>}
        <div className="alert-body">{children}</div>
      </div>
    </div>
  );
}

// ── CodeBlock ──────────────────────────────────────────────────────────────────
export function CodeBlock({ code, language = "html", onCopy }) {
  const [copied, setCopied] = React.useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    onCopy?.();
  };
  return (
    <div className="code-block">
      <div className="code-block-header">
        <span className="code-lang">{language}</span>
        <button className="copy-btn" onClick={handleCopy}>
          {copied ? "✓ Copied" : "Copy"}
        </button>
      </div>
      <pre className="code-pre"><code>{code}</code></pre>
    </div>
  );
}

// ── Spinner ────────────────────────────────────────────────────────────────────
export function Spinner({ size = "md" }) {
  return <span className={`spinner spinner--${size}`} />;
}

// ── StatusDot ──────────────────────────────────────────────────────────────────
export function StatusDot({ status }) {
  return <span className={`status-dot status-dot--${status}`} />;
}

// ── SectionHeader ──────────────────────────────────────────────────────────────
export function SectionHeader({ title, subtitle, action }) {
  return (
    <div className="section-header">
      <div>
        <h2 className="section-title">{title}</h2>
        {subtitle && <p className="section-subtitle">{subtitle}</p>}
      </div>
      {action && <div className="section-action">{action}</div>}
    </div>
  );
}

// ── Tabs ───────────────────────────────────────────────────────────────────────
export function Tabs({ tabs, active, onChange }) {
  return (
    <div className="tabs">
      {tabs.map((t) => (
        <button
          key={t.id}
          className={`tab ${active === t.id ? "tab--active" : ""}`}
          onClick={() => onChange(t.id)}
        >
          {t.icon && <span className="tab-icon">{t.icon}</span>}
          {t.label}
        </button>
      ))}
    </div>
  );
}
