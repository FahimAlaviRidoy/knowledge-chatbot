import { Link, useLocation, useNavigate } from 'react-router-dom'
import { MessageSquare, Database, LogOut, Shield, Cpu } from 'lucide-react'
import useAuthStore from '../store/authStore'
import './Layout.css'

export default function Layout({ children }) {
  const { user, logout } = useAuthStore()
  const location = useLocation()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <Cpu size={22} className="logo-icon" />
          <span className="logo-text">KnowledgeBot</span>
        </div>

        <nav className="sidebar-nav">
          <Link
            to="/chat"
            className={`nav-item ${location.pathname === '/chat' ? 'active' : ''}`}
          >
            <MessageSquare size={18} />
            <span>Chat</span>
          </Link>
          {user?.role === 'admin' && (
            <Link
              to="/admin"
              className={`nav-item ${location.pathname === '/admin' ? 'active' : ''}`}
            >
              <Database size={18} />
              <span>Knowledge Base</span>
            </Link>
          )}
        </nav>

        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-avatar">{user?.username?.[0]?.toUpperCase()}</div>
            <div className="user-details">
              <span className="user-name">{user?.username}</span>
              <span className={`badge badge-${user?.role}`}>{user?.role}</span>
            </div>
          </div>
          <button className="logout-btn" onClick={handleLogout} title="Logout">
            <LogOut size={16} />
          </button>
        </div>
      </aside>

      <main className="main-content">{children}</main>
    </div>
  )
}
