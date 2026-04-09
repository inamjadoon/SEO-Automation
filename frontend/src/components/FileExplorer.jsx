import React, { useState } from 'react'
import '../styles/FileExplorer.css'

// ── Helpers ──────────────────────────────────────────────────────────────────

function getFileIcon(filename) {
  const ext = filename.split('.').pop().toLowerCase()
  const map = {
    json:  '{}',
    html:  '<>',
    txt:   '📄',
    xml:   '⚙️',
    csv:   '📊',
    md:    '📝',
    js:    '⚡',
    css:   '🎨',
  }
  return map[ext] || '📁'
}

function formatBytes(bytes) {
  if (!bytes) return '—'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatType(filename) {
  const ext = filename.split('.').pop().toUpperCase()
  return ext
}

// ── Skeleton rows while loading ───────────────────────────────────────────────

function SkeletonRows() {
  return (
    <>
      {[120, 85, 200, 60, 140].map((w, i) => (
        <div key={i} className="file-skeleton">
          <div className="skeleton-bar" style={{ width: 20, height: 20, borderRadius: '50%' }} />
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 6 }}>
            <div className="skeleton-bar" style={{ width: `${w}px`, height: 12 }} />
            <div className="skeleton-bar" style={{ width: 60, height: 10 }} />
          </div>
          <div className="skeleton-bar" style={{ width: 36, height: 10 }} />
        </div>
      ))}
    </>
  )
}

// ── Main Component ────────────────────────────────────────────────────────────

/**
 * Props:
 *   files   — array of { name, size?, content?, type? } objects
 *             size    = number of bytes (optional)
 *             content = string preview content (optional)
 *             type    = label like "FAQ Schema", "JSON-LD" (optional)
 *   loading — boolean, shows skeleton rows
 *   domain  — string, shown in header
 */
export default function FileExplorer({ files = [], loading = false, domain = '' }) {
  const [activeFile, setActiveFile] = useState(null)

  const handleFileClick = (file) => {
    setActiveFile(prev => prev?.name === file.name ? null : file)
  }

  return (
    <div className="file-explorer">
      {/* Header */}
      <div className="file-explorer-header">
        <div className="file-explorer-title">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
          </svg>
          Generated Files
          {domain && (
            <span style={{ opacity: 0.5, fontWeight: 400, textTransform: 'none', letterSpacing: 0, fontSize: 11 }}>
              — {domain.replace(/^https?:\/\//, '')}
            </span>
          )}
        </div>
        {!loading && (
          <span className="file-count-badge">{files.length} file{files.length !== 1 ? 's' : ''}</span>
        )}
      </div>

      {/* File list */}
      <div className="file-list">
        {loading ? (
          <SkeletonRows />
        ) : files.length === 0 ? (
          <div className="file-explorer-empty">No files generated yet</div>
        ) : (
          files.map((file) => (
            <div
              key={file.name}
              className={`file-item ${activeFile?.name === file.name ? 'active' : ''}`}
              onClick={() => handleFileClick(file)}
            >
              <span className="file-icon">{getFileIcon(file.name)}</span>
              <div className="file-info">
                <div className="file-name">{file.name}</div>
                <div className="file-meta">
                  {file.type || formatType(file.name)}
                  {file.size ? ` · ${formatBytes(file.size)}` : ''}
                </div>
              </div>
              <span className="file-size">{formatBytes(file.size)}</span>
            </div>
          ))
        )}
      </div>

      {/* Inline preview */}
      {activeFile && activeFile.content && (
        <div className="file-preview">
          <div className="file-preview-bar">
            <span className="file-preview-name">{activeFile.name}</span>
            <button className="file-preview-close" onClick={() => setActiveFile(null)}>✕</button>
          </div>
          <div className="file-preview-content">
            {typeof activeFile.content === 'object'
              ? JSON.stringify(activeFile.content, null, 2)
              : activeFile.content}
          </div>
        </div>
      )}
    </div>
  )
}