import { ReactNode, useState } from 'react'
import { NavLink } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  LayoutDashboard,
  GitBranch,
  Users,
  Shield,
  MessageSquare,
  Activity,
  Keyboard,
} from 'lucide-react'
import { useActivityStore } from '../stores/activityStore'
import ChatPanel from './ChatPanel'
import PortfolioSelector from './PortfolioSelector'
import { getShortcutsList } from '../hooks/useKeyboard'

interface LayoutProps {
  children: ReactNode
}

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/scenarios', label: 'Scenarios', icon: GitBranch },
  { path: '/war-room', label: 'War Room', icon: Users },
  { path: '/audit', label: 'Audit Trail', icon: Shield },
]

export default function Layout({ children }: LayoutProps) {
  const { isConnected, activeAgents, chatOpen, setChatOpen, selectedPortfolioId, setSelectedPortfolioId, clearActivities } = useActivityStore()
  const [showShortcuts, setShowShortcuts] = useState(false)
  const shortcuts = getShortcutsList()

  // Handle portfolio change - clear previous analysis state
  const handlePortfolioChange = (portfolioId: string | null) => {
    if (portfolioId !== selectedPortfolioId) {
      clearActivities()
    }
    setSelectedPortfolioId(portfolioId)
  }

  return (
    <div className="min-h-screen bg-bg-primary flex">
      {/* Sidebar */}
      <aside className="w-64 bg-bg-secondary border-r border-border-subtle flex flex-col">
        {/* Logo */}
        <div className="h-16 flex items-center px-6 border-b border-border-subtle">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center gap-3"
          >
            <div className="w-8 h-8 rounded-lg bg-accent/10 border border-accent/30 flex items-center justify-center">
              <Activity className="w-4 h-4 text-accent" />
            </div>
            <div>
              <span className="text-sm font-bold text-text-primary tracking-wider">
                SENTINEL
              </span>
              <span className="text-xs text-accent ml-1">V2</span>
            </div>
          </motion.div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4 px-3">
          <ul className="space-y-1">
            {navItems.map((item, index) => (
              <motion.li
                key={item.path}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <NavLink
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                      isActive
                        ? 'bg-accent/10 text-accent border border-accent/20'
                        : 'text-text-secondary hover:bg-bg-tertiary hover:text-text-primary'
                    }`
                  }
                >
                  <item.icon className="w-4 h-4" />
                  {item.label}
                </NavLink>
              </motion.li>
            ))}
          </ul>
        </nav>

        {/* Agent Status */}
        <div className="p-4 border-t border-border-subtle">
          <div className="text-xs text-text-muted uppercase tracking-wider mb-3">
            Active Agents
          </div>
          <div className="space-y-2">
            {activeAgents.length > 0 ? (
              activeAgents.map((agent) => (
                <div
                  key={agent.name}
                  className="flex items-center gap-2 text-sm"
                >
                  <span className="status-dot status-dot-active" />
                  <span className="text-text-secondary">{agent.name}</span>
                </div>
              ))
            ) : (
              <div className="flex items-center gap-2 text-sm">
                <span className="status-dot status-dot-idle" />
                <span className="text-text-muted">All agents idle</span>
              </div>
            )}
          </div>
        </div>

        {/* Connection Status */}
        <div className="p-4 border-t border-border-subtle">
          <div className="flex items-center gap-2 text-xs">
            <span
              className={`status-dot ${
                isConnected ? 'status-dot-success' : 'status-dot-error'
              }`}
            />
            <span className="text-text-muted">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Top Bar */}
        <header className="h-16 bg-bg-secondary border-b border-border-subtle flex items-center justify-between px-6">
          <div className="flex items-center gap-4">
            <PortfolioSelector
              value={selectedPortfolioId}
              onChange={handlePortfolioChange}
            />
          </div>

          <div className="flex items-center gap-3">
            {/* Keyboard Shortcuts Help */}
            <div className="relative">
              <button
                onClick={() => setShowShortcuts(!showShortcuts)}
                className="btn-ghost p-2 text-text-muted hover:text-text-primary"
                title="Keyboard Shortcuts"
              >
                <Keyboard className="w-5 h-5" />
              </button>
              {showShortcuts && (
                <>
                  <div
                    className="fixed inset-0 z-40"
                    onClick={() => setShowShortcuts(false)}
                  />
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="absolute right-0 top-full mt-2 w-48 bg-bg-elevated border border-border-subtle rounded-lg shadow-card-hover z-50 p-3"
                  >
                    <p className="text-xs text-text-muted uppercase tracking-wider mb-2">
                      Keyboard Shortcuts
                    </p>
                    <div className="space-y-1.5">
                      {shortcuts.map((s) => (
                        <div key={s.keys} className="flex items-center justify-between text-sm">
                          <span className="text-text-secondary">{s.description}</span>
                          <kbd className="px-1.5 py-0.5 text-xs bg-bg-tertiary border border-border-subtle rounded font-mono">
                            {s.keys}
                          </kbd>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                </>
              )}
            </div>

            {/* Chat Toggle */}
            <button
              onClick={() => setChatOpen(!chatOpen)}
              className={`btn-ghost p-2 ${chatOpen ? 'text-accent' : ''}`}
              title="Toggle Chat (⌘K)"
            >
              <MessageSquare className="w-5 h-5" />
            </button>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-auto">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="p-6"
          >
            {children}
          </motion.div>
        </main>
      </div>

      {/* Chat Panel (Slide-in) */}
      <ChatPanel isOpen={chatOpen} onClose={() => setChatOpen(false)} />
    </div>
  )
}
