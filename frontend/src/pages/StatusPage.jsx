import React, { useState, useEffect, useRef } from 'react'
import StepTracker, { STEPS } from '../components/StepTracker.jsx'
import SnippetResult          from '../components/SnippetResult.jsx'
import FileExplorer           from '../components/FileExplorer.jsx'
import '../styles/StatusPage.css'

// ── Helpers ───────────────────────────────────────────────────────────────────

/**
 * Fetches the list of generated files for a site.
 * Your backend should expose GET /sites/{site_id}/files
 * returning an array of { name, size, content?, type? }.
 *
 * If your backend doesn't have this endpoint yet, remove the call
 * and the FileExplorer will render empty / loading.
 */
async function fetchFiles(siteId) {
  const res = await fetch(`http://localhost:8000/sites/auto-register/${siteId}/files`)
  if (!res.ok) return []
  return res.json()
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function StatusPage({ siteId, domain, onReset }) {
  const [currentStep,   setCurrentStep]   = useState(0)
  const [snippet,       setSnippet]       = useState(null)
  const [files,         setFiles]         = useState([])
  const [filesLoading,  setFilesLoading]  = useState(false)

  const pollRef = useRef(null)
  const stepRef = useRef(null)

  useEffect(() => {
    // ── Advance visual steps every 4 s ──────────────────────────────────────
    stepRef.current = setInterval(() => {
      setCurrentStep(prev => (prev < STEPS.length - 1 ? prev + 1 : prev))
    }, 4000)

    // ── Poll for snippet (every 5 s) ─────────────────────────────────────────
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(
          `http://localhost:8000/sites/auto-register/${siteId}/snippet`
        )

        if (res.status === 200) {
          const html = await res.text()
          setSnippet(html)
          setCurrentStep(STEPS.length - 1)
          clearInterval(pollRef.current)
          clearInterval(stepRef.current)

          // Fetch generated files once snippet is ready
          setFilesLoading(true)
          try {
            const fileList = await fetchFiles(siteId)
            setFiles(fileList)
          } catch (e) {
            console.warn('Could not fetch files:', e)
          } finally {
            setFilesLoading(false)
          }
        }
        // 202 → still processing, keep polling
      } catch (err) {
        console.warn('Poll error:', err.message)
      }
    }, 5000)

    return () => {
      clearInterval(pollRef.current)
      clearInterval(stepRef.current)
    }
  }, [siteId])

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="status-page">
      <div className="status-card">

        {/* ── Processing view ─────────────────────────────────────────────── */}
        {!snippet && (
          <>
            <div className="status-header">
              <h2 className="status-title">Setting up your site</h2>
              <p className="status-sub">This usually takes 1–2 minutes. Stay on this page.</p>
              {domain && (
                <div className="status-domain-tag">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="2" y1="12" x2="22" y2="12"/>
                    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
                  </svg>
                  {domain.replace(/^https?:\/\//, '')}
                </div>
              )}
            </div>

            <StepTracker currentStep={currentStep} />
          </>
        )}

        {/* ── Snippet ready ────────────────────────────────────────────────── */}
        {snippet && (
          <>
            <SnippetResult snippet={snippet} onReset={onReset} />

            {/* Divider + file explorer */}
            <div className="status-divider" />
            <FileExplorer
              files={files}
              loading={filesLoading}
              domain={domain}
            />
          </>
        )}

      </div>
    </div>
  )
}