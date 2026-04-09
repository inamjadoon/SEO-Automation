import React, { useState } from 'react'
import '../styles/RegisterPage.css'

export default function RegisterPage({ onSubmitted }) {
  const [siteId, setSiteId] = useState('')
  const [domain, setDomain] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError]   = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const res = await fetch('http://localhost:8000/sites/auto-register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ site_id: siteId, domain }),
      })

      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Something went wrong')
      }

      // Hand off site info to parent — it will switch to StatusPage
      onSubmitted({ siteId, domain })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="register-page">
      <div className="register-card">
        <div className="register-badge">
          <span className="register-badge-dot" />
          SEO Auto-Register
        </div>

        <h1 className="register-title">Register your site</h1>
        <p className="register-sub">Enter your site details to generate your SEO snippet.</p>

        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="site-id">Site ID</label>
            <input
              id="site-id"
              type="text"
              value={siteId}
              onChange={e => setSiteId(e.target.value)}
              placeholder="e.g. sq-a1b2c3d4"
              required
              autoComplete="off"
            />
          </div>

          <div className="field">
            <label htmlFor="domain">Domain</label>
            <input
              id="domain"
              type="text"
              value={domain}
              onChange={e => setDomain(e.target.value)}
              placeholder="e.g. https://mybusiness.com"
              required
              autoComplete="off"
            />
          </div>

          {error && <p className="register-error">{error}</p>}

          <button className="register-btn" type="submit" disabled={loading}>
            {loading ? 'Submitting…' : 'Generate SEO Snippet →'}
          </button>
        </form>
      </div>
    </div>
  )
}