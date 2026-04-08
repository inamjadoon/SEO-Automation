// import React, { useState } from 'react'

// export default function App() {
//   const [siteId, setSiteId] = useState('')
//   const [domain, setDomain] = useState('')
//   const [loading, setLoading] = useState(false)
//   const [error, setError] = useState(null)
//   const [snippet, setSnippet] = useState(null)

//   async function handleSubmit(e) {
//     e.preventDefault()
//     setError(null)
//     setLoading(true)

//     try {
//       const res = await fetch('http://localhost:8000/sites/auto-register', {
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json' },
//         body: JSON.stringify({ site_id: siteId, domain: domain })
//       })

//       if (!res.ok) {
//         const err = await res.json()
//         throw new Error(err.detail || 'Something went wrong')
//       }

//       // Your backend returns raw HTML, not JSON
//       const html = await res.text()
//       setSnippet(html)

//     } catch (err) {
//       setError(err.message)
//     } finally {
//       setLoading(false)
//     }
//   }

//   // If we got the snippet back, show it
//   if (snippet) {
//     return (
//       <div style={{ padding: '40px', maxWidth: '700px', margin: '0 auto' }}>
//         <h2>Your Squarespace Snippet</h2>
//         <p>Copy this and paste it into Squarespace → Settings → Advanced → Code Injection → Header</p>
//         <textarea
//           readOnly
//           value={snippet}
//           style={{ width: '100%', height: '200px', fontFamily: 'monospace', marginTop: '16px' }}
//         />
//         <br />
//         <button onClick={() => setSnippet(null)} style={{ marginTop: '12px' }}>
//           ← Register another site
//         </button>
//       </div>
//     )
//   }

//   // Otherwise show the form
//   return (
//     <div style={{ padding: '40px', maxWidth: '500px', margin: '0 auto' }}>
//       <h1>Register your site</h1>
//       <form onSubmit={handleSubmit}>
//         <div style={{ marginBottom: '16px' }}>
//           <label>Site ID</label><br />
//           <input
//             type="text"
//             value={siteId}
//             onChange={e => setSiteId(e.target.value)}
//             placeholder="e.g. sq-a1b2c3d4"
//             required
//             style={{ width: '100%', padding: '8px', marginTop: '4px' }}
//           />
//         </div>

//         <div style={{ marginBottom: '16px' }}>
//           <label>Domain</label><br />
//           <input
//             type="text"
//             value={domain}
//             onChange={e => setDomain(e.target.value)}
//             placeholder="e.g. https://mybusiness.com"
//             required
//             style={{ width: '100%', padding: '8px', marginTop: '4px' }}
//           />
//         </div>

//         {error && <p style={{ color: 'red' }}>{error}</p>}

//         <button type="submit" disabled={loading} style={{ padding: '10px 24px' }}>
//           {loading ? 'Connecting...' : 'Generate Snippet'}
//         </button>
//       </form>
//     </div>
//   )
// }

import React, { useState, useEffect, useRef } from 'react'

// These are the steps we want to show the user
// We'll light them up one by one as time passes while backend is working
const STEPS = [
  { id: 'registered',  label: 'Site registered in database' },
  { id: 'crawling',    label: 'Crawling your website' },
  { id: 'faq',         label: 'Generating FAQ schema' },
  { id: 'jsonld',      label: 'Building JSON-LD structured data' },
  { id: 'snippet',     label: 'Preparing Squarespace snippet' },
]

export default function App() {
  const [siteId, setSiteId]   = useState('')
  const [domain, setDomain]   = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState(null)

  // Once form submitted, we move to "status" view
  const [submitted, setSubmitted] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [snippet, setSnippet] = useState(null)
  const [copied, setCopied]   = useState(false)

  const pollRef    = useRef(null)   // holds the setInterval id
  const stepRef    = useRef(null)   // holds the step-advance interval id
  const submittedSiteId = useRef('') // remember which site_id to poll

  // ── Start polling once form is submitted ──────────────────────────────────
  useEffect(() => {
    if (!submitted) return

    // Advance the visual steps every 4 seconds regardless
    // This gives user feedback even while backend is working
    stepRef.current = setInterval(() => {
      setCurrentStep(prev => {
        if (prev < STEPS.length - 1) return prev + 1
        return prev
      })
    }, 4000)

    // Poll the snippet endpoint every 5 seconds
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(
          `http://localhost:8000/sites/auto-register/${submittedSiteId.current}/snippet`
        )

        if (res.status === 200) {
          // Backend says it's ready
          const html = await res.text()
          setSnippet(html)
          setCurrentStep(STEPS.length - 1) // mark all steps done
          clearInterval(pollRef.current)
          clearInterval(stepRef.current)
        }
        // 202 means still pending — just keep polling

      } catch (err) {
        // network error — just keep trying
        console.log('Poll error:', err.message)
      }
    }, 5000)

    // Cleanup on unmount
    return () => {
      clearInterval(pollRef.current)
      clearInterval(stepRef.current)
    }
  }, [submitted])

  // ── Form submit ───────────────────────────────────────────────────────────
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

      // Save the site_id so the polling useEffect can use it
      submittedSiteId.current = siteId

      // Move to status view immediately — don't wait for snippet
      setSubmitted(true)
      setCurrentStep(0)

    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function handleCopy() {
    navigator.clipboard.writeText(snippet)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  function handleReset() {
    setSiteId('')
    setDomain('')
    setSubmitted(false)
    setSnippet(null)
    setCurrentStep(0)
    setCopied(false)
    clearInterval(pollRef.current)
    clearInterval(stepRef.current)
  }

  // ── View 1: Form ──────────────────────────────────────────────────────────
  if (!submitted) {
    return (
      <div style={styles.page}>
        <div style={styles.card}>
          <h1 style={styles.title}>Register your site</h1>
          <p style={styles.subtitle}>Enter your site details to generate your SEO snippet</p>

          <form onSubmit={handleSubmit}>
            <div style={styles.field}>
              <label style={styles.label}>Site ID</label>
              <input
                style={styles.input}
                type="text"
                value={siteId}
                onChange={e => setSiteId(e.target.value)}
                placeholder="e.g. sq-a1b2c3d4"
                required
              />
            </div>

            <div style={styles.field}>
              <label style={styles.label}>Domain</label>
              <input
                style={styles.input}
                type="text"
                value={domain}
                onChange={e => setDomain(e.target.value)}
                placeholder="e.g. https://mybusiness.com"
                required
              />
            </div>

            {error && <p style={styles.error}>{error}</p>}

            <button style={styles.btn} type="submit" disabled={loading}>
              {loading ? 'Submitting...' : 'Generate SEO Snippet →'}
            </button>
          </form>
        </div>
      </div>
    )
  }

  // ── View 2: Status + Steps ────────────────────────────────────────────────
  if (submitted && !snippet) {
    return (
      <div style={styles.page}>
        <div style={styles.card}>
          <h2 style={styles.title}>Setting up your site</h2>
          <p style={styles.subtitle}>
            This usually takes 1–2 minutes. You can stay on this page.
          </p>

          <div style={styles.stepsContainer}>
            {STEPS.map((step, index) => {
              const isDone    = index < currentStep
              const isCurrent = index === currentStep
              const isPending = index > currentStep

              return (
                <div key={step.id} style={styles.stepRow}>
                  {/* Circle indicator */}
                  <div style={{
                    ...styles.stepCircle,
                    background: isDone    ? '#22c55e' :
                                isCurrent ? '#3b82f6' : '#e5e7eb',
                    color:      isDone || isCurrent ? '#fff' : '#9ca3af',
                  }}>
                    {isDone ? '✓' : index + 1}
                  </div>

                  {/* Label + status */}
                  <div style={styles.stepContent}>
                    <span style={{
                      ...styles.stepLabel,
                      color: isPending ? '#9ca3af' : '#111827'
                    }}>
                      {step.label}
                    </span>
                    <span style={{
                      ...styles.stepStatus,
                      color: isDone    ? '#22c55e' :
                             isCurrent ? '#3b82f6' : '#d1d5db'
                    }}>
                      {isDone    ? 'Done' :
                       isCurrent ? 'In progress...' : 'Pending'}
                    </span>
                  </div>

                  {/* Spinner on current step */}
                  {isCurrent && (
                    <div style={styles.spinner} />
                  )}
                </div>
              )
            })}
          </div>
        </div>
      </div>
    )
  }

  // ── View 3: Snippet ready ─────────────────────────────────────────────────
  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <div style={styles.successBadge}>All done</div>
        <h2 style={styles.title}>Your snippet is ready</h2>
        <p style={styles.subtitle}>
          Paste this into Squarespace → Settings → Advanced → Code Injection → Header
        </p>

        <div style={styles.snippetBox}>
          <textarea
            readOnly
            value={snippet}
            style={styles.textarea}
          />
          <button style={styles.copyBtn} onClick={handleCopy}>
            {copied ? '✓ Copied!' : 'Copy'}
          </button>
        </div>

        <button style={styles.ghostBtn} onClick={handleReset}>
          ← Register another site
        </button>
      </div>
    </div>
  )
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = {
  page: {
    minHeight: '100vh',
    background: '#f9fafb',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '24px',
    fontFamily: 'sans-serif',
  },
  card: {
    background: '#fff',
    borderRadius: '12px',
    padding: '40px',
    width: '100%',
    maxWidth: '520px',
    boxShadow: '0 4px 24px rgba(0,0,0,0.08)',
  },
  title: { fontSize: '22px', fontWeight: '700', marginBottom: '8px', color: '#111827' },
  subtitle: { fontSize: '14px', color: '#6b7280', marginBottom: '28px' },
  field: { marginBottom: '18px' },
  label: { display: 'block', fontSize: '13px', fontWeight: '600', color: '#374151', marginBottom: '6px' },
  input: { width: '100%', padding: '10px 12px', border: '1px solid #d1d5db', borderRadius: '8px', fontSize: '15px', outline: 'none', boxSizing: 'border-box' },
  error: { color: '#ef4444', fontSize: '13px', marginBottom: '12px' },
  btn: { width: '100%', padding: '12px', background: '#3b82f6', color: '#fff', border: 'none', borderRadius: '8px', fontSize: '15px', fontWeight: '600', cursor: 'pointer' },
  stepsContainer: { display: 'flex', flexDirection: 'column', gap: '16px' },
  stepRow: { display: 'flex', alignItems: 'center', gap: '14px' },
  stepCircle: { width: '32px', height: '32px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '13px', fontWeight: '700', flexShrink: 0 },
  stepContent: { flex: 1, display: 'flex', flexDirection: 'column', gap: '2px' },
  stepLabel: { fontSize: '14px', fontWeight: '500' },
  stepStatus: { fontSize: '12px' },
  spinner: { width: '18px', height: '18px', border: '2px solid #e5e7eb', borderTopColor: '#3b82f6', borderRadius: '50%', animation: 'spin 0.7s linear infinite', flexShrink: 0 },
  snippetBox: { position: 'relative', marginBottom: '16px' },
  textarea: { width: '100%', height: '180px', fontFamily: 'monospace', fontSize: '12px', padding: '12px', border: '1px solid #e5e7eb', borderRadius: '8px', resize: 'none', background: '#f9fafb', boxSizing: 'border-box' },
  copyBtn: { position: 'absolute', top: '10px', right: '10px', padding: '6px 14px', background: '#111827', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '12px' },
  ghostBtn: { background: 'none', border: 'none', color: '#6b7280', cursor: 'pointer', fontSize: '14px', padding: '0' },
  successBadge: { display: 'inline-block', background: '#dcfce7', color: '#16a34a', padding: '4px 12px', borderRadius: '99px', fontSize: '12px', fontWeight: '600', marginBottom: '14px' },
}