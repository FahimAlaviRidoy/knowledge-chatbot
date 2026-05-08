import { useState, useEffect, useRef } from 'react'
import {
  Upload, Trash2, Globe, FileText, Database,
  RefreshCw, Users, CheckCircle, AlertCircle
} from 'lucide-react'
import toast from 'react-hot-toast'
import { knowledgeApi, adminApi } from '../services/api'
import './AdminPage.css'

function StatCard({ icon: Icon, label, value, accent }) {
  return (
    <div className="stat-card">
      <div className="stat-icon" style={{ '--c': accent }}><Icon size={20} /></div>
      <div>
        <div className="stat-value">{value ?? '—'}</div>
        <div className="stat-label">{label}</div>
      </div>
    </div>
  )
}

export default function AdminPage() {
  const [docs, setDocs] = useState([])
  const [stats, setStats] = useState(null)
  const [users, setUsers] = useState([])
  const [activeSessions, setActiveSessions] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [urlInput, setUrlInput] = useState('')
  const [urlTitle, setUrlTitle] = useState('')
  const [ingestingUrl, setIngestingUrl] = useState(false)
  const [tab, setTab] = useState('documents')
  const fileRef = useRef()

  const refresh = async () => {
    try {
      const [docsRes, statsRes, usersRes, sessRes] = await Promise.all([
        knowledgeApi.listDocuments(),
        knowledgeApi.getStats(),
        adminApi.listUsers(),
        adminApi.activeSessions(),
      ])
      setDocs(docsRes.data)
      setStats(statsRes.data)
      setUsers(usersRes.data)
      setActiveSessions(sessRes.data.active_sessions)
    } catch (err) {
      toast.error('Failed to load data')
    }
  }

  useEffect(() => { refresh() }, [])

  const handleFileUpload = async (e) => {
    const files = Array.from(e.target.files)
    if (!files.length) return
    setUploading(true)
    let success = 0
    for (const file of files) {
      try {
        const { data } = await knowledgeApi.uploadFile(file)
        toast.success(`${file.name}: ${data.chunks_created} chunks indexed`)
        success++
      } catch (err) {
        toast.error(`${file.name}: ${err.response?.data?.detail || 'Upload failed'}`)
      }
    }
    setUploading(false)
    fileRef.current.value = ''
    if (success > 0) refresh()
  }

  const handleIngestUrl = async () => {
    if (!urlInput.trim()) return
    setIngestingUrl(true)
    try {
      const { data } = await knowledgeApi.ingestUrl(urlInput.trim(), urlTitle.trim() || null)
      toast.success(`Ingested: ${data.chunks_created} chunks`)
      setUrlInput('')
      setUrlTitle('')
      refresh()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'URL ingest failed')
    } finally {
      setIngestingUrl(false)
    }
  }

  const handleDelete = async (doc) => {
    if (!confirm(`Delete "${doc.filename}"?`)) return
    try {
      await knowledgeApi.deleteDocument(doc.doc_id)
      toast.success('Document deleted')
      refresh()
    } catch {
      toast.error('Delete failed')
    }
  }

  const fmtDate = (iso) => iso ? new Date(iso).toLocaleDateString() : '—'
  const fmtSize = (b) => b > 1024*1024 ? `${(b/1024/1024).toFixed(1)}MB` : `${Math.round(b/1024)}KB`

  return (
    <div className="admin-page">
      <div className="admin-header">
        <h1 className="admin-title">Knowledge Base</h1>
        <button className="btn btn-ghost" onClick={refresh}><RefreshCw size={14} /> Refresh</button>
      </div>

      {/* Stats */}
      <div className="stats-grid">
        <StatCard icon={Database} label="Documents" value={stats?.total_documents} accent="var(--accent)" />
        <StatCard icon={FileText} label="Chunks" value={stats?.total_chunks} accent="var(--accent2)" />
        <StatCard icon={Users} label="Users" value={users.length} accent="#ffb347" />
        <StatCard icon={CheckCircle} label="Active Sessions" value={activeSessions} accent="#ff4d6a" />
      </div>

      {/* Tabs */}
      <div className="tabs">
        {['documents', 'upload', 'users'].map((t) => (
          <button key={t} className={`tab ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {/* Documents tab */}
      {tab === 'documents' && (
        <div className="tab-content">
          {docs.length === 0 ? (
            <div className="empty-state">
              <Database size={40} />
              <p>No documents in the knowledge base yet.</p>
              <button className="btn btn-primary" onClick={() => setTab('upload')}>
                <Upload size={14} /> Upload your first document
              </button>
            </div>
          ) : (
            <table className="docs-table">
              <thead>
                <tr>
                  <th>Filename</th>
                  <th>Type</th>
                  <th>Chunks</th>
                  <th>Size</th>
                  <th>Uploaded</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {docs.map((doc) => (
                  <tr key={doc.doc_id}>
                    <td className="doc-name">{doc.filename}</td>
                    <td><code className="type-badge">{doc.file_type}</code></td>
                    <td className="num">{doc.chunks}</td>
                    <td className="num">{fmtSize(doc.size_bytes)}</td>
                    <td className="dim">{fmtDate(doc.uploaded_at)}</td>
                    <td>
                      <button className="icon-btn danger" onClick={() => handleDelete(doc)}>
                        <Trash2 size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Upload tab */}
      {tab === 'upload' && (
        <div className="tab-content upload-section">
          {/* File upload */}
          <div className="upload-card">
            <h3 className="upload-card-title"><Upload size={16} /> Upload Files</h3>
            <p className="upload-card-desc">
              Supported: PDF, DOCX, TXT, MD, HTML/HTM — up to 50MB each.
            </p>
            <div
              className="drop-zone"
              onClick={() => fileRef.current.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault()
                const dt = { target: { files: e.dataTransfer.files } }
                handleFileUpload(dt)
              }}
            >
              <Upload size={32} />
              <p>{uploading ? 'Uploading…' : 'Click or drag files here'}</p>
            </div>
            <input
              ref={fileRef}
              type="file"
              multiple
              accept=".pdf,.docx,.txt,.md,.html,.htm"
              style={{ display: 'none' }}
              onChange={handleFileUpload}
              disabled={uploading}
            />
          </div>

          {/* URL ingest */}
          <div className="upload-card">
            <h3 className="upload-card-title"><Globe size={16} /> Ingest from URL</h3>
            <p className="upload-card-desc">Scrape and index any public web page.</p>
            <div className="url-form">
              <input
                className="input"
                placeholder="https://example.com/page"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
              />
              <input
                className="input"
                placeholder="Custom title (optional)"
                value={urlTitle}
                onChange={(e) => setUrlTitle(e.target.value)}
              />
              <button
                className="btn btn-primary"
                onClick={handleIngestUrl}
                disabled={!urlInput.trim() || ingestingUrl}
              >
                <Globe size={14} />
                {ingestingUrl ? 'Ingesting…' : 'Ingest URL'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Users tab */}
      {tab === 'users' && (
        <div className="tab-content">
          <table className="docs-table">
            <thead>
              <tr>
                <th>Username</th>
                <th>Email</th>
                <th>Role</th>
                <th>Joined</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td><strong>{u.username}</strong></td>
                  <td className="dim">{u.email}</td>
                  <td><span className={`badge badge-${u.role}`}>{u.role}</span></td>
                  <td className="dim">{fmtDate(u.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
