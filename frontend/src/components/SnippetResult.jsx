import React, { useState } from 'react'
import '../styles/SnippetResult.css'

export default function SnippetResult({ snippet, onReset }) {
  const [copied, setCopied] = useState(false)

  function handleCopy() {
    navigator.clipboard.writeText(snippet)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="snippet-result">
      <div className="snippet-success-badge">
        <span>✓</span> All done
      </div>

      <h2 className="snippet-title">Your snippet is ready</h2>
      <p className="snippet-sub">Paste this into your Squarespace site Header to enable SEO structured data.</p>

      {/* Instruction callout */}
      <div className="snippet-instruction">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ flexShrink: 0, marginTop: 1 }}>
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <strong style={{ margin: '0 3px' }}>Settings → Advanced → Code Injection → Header</strong> 
      </div>

      {/* Code box */}
      <div className="snippet-box">
        <textarea
          className="snippet-textarea"
          readOnly
          value={snippet}
          spellCheck={false}
        />
        <button
          className={`snippet-copy-btn ${copied ? 'copied' : ''}`}
          onClick={handleCopy}
        >
          {copied ? '✓ Copied!' : 'Copy'}
        </button>
      </div>

      <button className="snippet-reset-btn" onClick={onReset}>
        ← Register another site
      </button>
    </div>
  )
}