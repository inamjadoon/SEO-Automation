import React, { useState } from 'react'
import '../styles/FileExplorer.css'

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatBytes(bytes) {
  if (!bytes) return '—'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

// ── Skeleton ──────────────────────────────────────────────────────────────────

function SkeletonRows() {
  return (
    <div className="file-group">
      <div className="file-group-header">
        <div className="skeleton-bar" style={{ width: 80, height: 11 }} />
        <div className="skeleton-bar" style={{ width: 24, height: 11 }} />
      </div>
      {[140, 100, 180, 80, 120].map((w, i) => (
        <div key={i} className="file-skeleton">
          <div className="skeleton-bar" style={{ width: 22, height: 22, borderRadius: '50%' }} />
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 5 }}>
            <div className="skeleton-bar" style={{ width: w, height: 12 }} />
            <div className="skeleton-bar" style={{ width: 60, height: 10 }} />
          </div>
          <div className="skeleton-bar" style={{ width: 38, height: 10 }} />
        </div>
      ))}
    </div>
  )
}

// ── Preview Panel (fetches content live from URL) ─────────────────────────────

function PreviewPanel({ file, onClose }) {
  const [content, setContent] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState(null)

  React.useEffect(() => {
    if (!file?.url) return
    setContent(null)
    setError(null)
    setLoading(true)

    fetch(file.url, {
      headers: { 'ngrok-skip-browser-warning': 'true' }
    })
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        const ct = r.headers.get('content-type') || ''
        return ct.includes('json') ? r.json() : r.text()
      })
      .then(data => {
        setContent(typeof data === 'object' ? JSON.stringify(data, null, 2) : data)
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [file?.url])

  return (
    <div className="file-preview">
      <div className="file-preview-bar">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <span className="file-preview-name">{file.name}</span>
          {file.page_path && (
            <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{file.page_path}</span>
          )}
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <a
            href={file.url}
            target="_blank"
            rel="noopener noreferrer"
            className="file-preview-open"
          >
            ↗ Open
          </a>
          <button className="file-preview-close" onClick={onClose}>✕</button>
        </div>
      </div>
      <div className="file-preview-content">
        {loading && <span style={{ color: 'var(--text-muted)' }}>Loading…</span>}
        {error   && <span style={{ color: 'var(--red)' }}>Could not load: {error}</span>}
        {content && content}
      </div>
    </div>
  )
}

// ── Single file row ───────────────────────────────────────────────────────────

function FileRow({ file, isActive, onClick }) {
  return (
    <div className={`file-item ${isActive ? 'active' : ''}`} onClick={onClick}>
      <div className="file-info">
        <div className="file-name">{file.name}</div>
        {file.page_path && <div className="file-meta">{file.page_path}</div>}
      </div>
      <span className="file-size">{formatBytes(file.size)}</span>
    </div>
  )
}

// ── Collapsible group ─────────────────────────────────────────────────────────

function FileGroup({ group, activeFile, onFileClick }) {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div className="file-group">
      <div className="file-group-header" onClick={() => setCollapsed(c => !c)}>
        <div className="file-group-label">
          <span className="file-group-icon">{group.icon}</span>
          {group.label}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span className="file-count-badge">{group.files.length}</span>
          <span className="file-group-chevron">{collapsed ? '▸' : '▾'}</span>
        </div>
      </div>

      {!collapsed && group.files.map(file => (
        <FileRow
          key={`${file.name}-${file.url}`}
          file={file}
          isActive={activeFile?.url === file.url}
          onClick={() => onFileClick(file)}
        />
      ))}
    </div>
  )
}

// ── Main Component ────────────────────────────────────────────────────────────

/**
 * Props:
 *   data    — response from GET /auto-register/{site_id}/files
 *             { site_id, total_files, groups: [{ type, label, icon, files[] }] }
 *   loading — boolean, shows skeleton
 *   domain  — string, shown in header
 */
export default function FileExplorer({ data = null, loading = false, domain = '' }) {
  const [activeFile, setActiveFile] = useState(null)

  const handleFileClick = (file) => {
    setActiveFile(prev => prev?.url === file.url ? null : file)
  }

  const groups     = data?.groups     || []
  const totalFiles = data?.total_files ?? 0

  return (
    <div className="file-explorer">
      {/* ── Header ── */}
      <div className="file-explorer-header">
        <div className="file-explorer-title">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
          </svg>
          Generated Files
          {domain && (
            <span className="file-explorer-domain">
              — {domain.replace(/^https?:\/\//, '')}
            </span>
          )}
        </div>
        {!loading && (
          <span className="file-count-badge">
            {totalFiles} file{totalFiles !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      {/* ── File groups ── */}
      <div className="file-list">
        {loading ? (
          <SkeletonRows />
        ) : groups.length === 0 ? (
          <div className="file-explorer-empty">No files generated yet</div>
        ) : (
          groups.map(group => (
            <FileGroup
              key={group.type}
              group={group}
              activeFile={activeFile}
              onFileClick={handleFileClick}
            />
          ))
        )}
      </div>

      {/* ── Inline preview ── */}
      {activeFile && (
        <PreviewPanel
          file={activeFile}
          onClose={() => setActiveFile(null)}
        />
      )}
    </div>
  )
}