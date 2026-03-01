import { Routes, Route, useNavigate } from 'react-router-dom'
import React, { useEffect } from 'react'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Scenarios from './pages/Scenarios'
import WarRoom from './pages/WarRoom'
import AuditTrail from './pages/AuditTrail'
import { useWebSocket } from './hooks/useWebSocket'
import { useActivityStore } from './stores/activityStore'
import { useKeyboardShortcuts } from './hooks/useKeyboard'
import { ToastProvider } from './components/ui/Toast'
import ErrorBoundary from './components/ErrorBoundary'
import CommandPalette from './components/CommandPalette'

function AppContent() {
  const navigate = useNavigate()
  const { connect, disconnect } = useWebSocket()
  const { setConnected } = useActivityStore()
  const connectedRef = React.useRef(false)

  // Enable keyboard shortcuts
  useKeyboardShortcuts()

  useEffect(() => {
    // Only connect once on mount
    if (connectedRef.current) return
    connectedRef.current = true

    connect()
      .then(() => setConnected(true))
      .catch(console.error)

    return () => {
      disconnect()
      setConnected(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/scenarios" element={<Scenarios />} />
        <Route path="/war-room" element={<WarRoom />} />
        <Route path="/audit" element={<AuditTrail />} />
      </Routes>
      <CommandPalette onNavigate={(path) => navigate(path)} />
    </Layout>
  )
}

function App() {
  return (
    <ErrorBoundary>
      <ToastProvider>
        <AppContent />
      </ToastProvider>
    </ErrorBoundary>
  )
}

export default App
