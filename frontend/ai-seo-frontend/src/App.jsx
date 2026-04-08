import React, { useState } from 'react'

export default function App() {
  const [siteId, setSiteId] = useState('')
  const [domain, setDomain] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [snippet, setSnippet] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const res = await fetch('http://localhost:8000/sites/auto-register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ site_id: siteId, domain: domain })
      })

      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Something went wrong')
      }

      // Your backend returns raw HTML, not JSON
      const html = await res.text()
      setSnippet(html)

    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // If we got the snippet back, show it
  if (snippet) {
    return (
      <div style={{ padding: '40px', maxWidth: '700px', margin: '0 auto' }}>
        <h2>Your Squarespace Snippet</h2>
        <p>Copy this and paste it into Squarespace → Settings → Advanced → Code Injection → Header</p>
        <textarea
          readOnly
          value={snippet}
          style={{ width: '100%', height: '200px', fontFamily: 'monospace', marginTop: '16px' }}
        />
        <br />
        <button onClick={() => setSnippet(null)} style={{ marginTop: '12px' }}>
          ← Register another site
        </button>
      </div>
    )
  }

  // Otherwise show the form
  return (
    <div style={{ padding: '40px', maxWidth: '500px', margin: '0 auto' }}>
      <h1>Register your site</h1>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '16px' }}>
          <label>Site ID</label><br />
          <input
            type="text"
            value={siteId}
            onChange={e => setSiteId(e.target.value)}
            placeholder="e.g. sq-a1b2c3d4"
            required
            style={{ width: '100%', padding: '8px', marginTop: '4px' }}
          />
        </div>

        <div style={{ marginBottom: '16px' }}>
          <label>Domain</label><br />
          <input
            type="text"
            value={domain}
            onChange={e => setDomain(e.target.value)}
            placeholder="e.g. https://mybusiness.com"
            required
            style={{ width: '100%', padding: '8px', marginTop: '4px' }}
          />
        </div>

        {error && <p style={{ color: 'red' }}>{error}</p>}

        <button type="submit" disabled={loading} style={{ padding: '10px 24px' }}>
          {loading ? 'Connecting...' : 'Generate Snippet'}
        </button>
      </form>
    </div>
  )
}