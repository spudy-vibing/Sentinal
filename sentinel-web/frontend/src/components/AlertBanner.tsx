import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  AlertTriangle,
  TrendingDown,
  Clock,
  X,
  ChevronRight,
  Zap,
  Bell,
  Loader2,
} from 'lucide-react'
import { useActivityStore } from '../stores/activityStore'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface ProactiveAlert {
  id: string
  type: 'market_move' | 'drift_detected' | 'tax_deadline' | 'rebalance_needed'
  severity: 'info' | 'warning' | 'critical'
  title: string
  description: string
  affectedPortfolios: string[]
  timestamp: string
  actionLabel?: string
  dismissed?: boolean
  eventType?: string  // For triggering analysis
}

// Simulated proactive alerts for demo
const DEMO_ALERTS: ProactiveAlert[] = [
  {
    id: 'alert_1',
    type: 'market_move',
    severity: 'warning',
    title: 'Tech Sector Down 4.2% Overnight',
    description: 'NVDA -5.3%, AMD -4.1%, MSFT -3.2%. 2 portfolios exceed drift thresholds.',
    affectedPortfolios: ['portfolio_a', 'portfolio_c'],
    timestamp: new Date().toISOString(),
    actionLabel: 'Review Impact',
    eventType: 'tech_crash',
  },
  {
    id: 'alert_2',
    type: 'tax_deadline',
    severity: 'info',
    title: 'Wash Sale Window Closing',
    description: 'NVDA wash sale window closes in 15 days. Tax-loss harvesting opportunity available.',
    affectedPortfolios: ['portfolio_a'],
    timestamp: new Date().toISOString(),
    actionLabel: 'View Opportunities',
    eventType: 'tax_review',
  },
]

export default function AlertBanner() {
  const [alerts, setAlerts] = useState<ProactiveAlert[]>([])
  const [currentAlertIndex, setCurrentAlertIndex] = useState(0)
  const [isLoading, setIsLoading] = useState(false)
  const { selectedPortfolioId, clearActivities, setSelectedPortfolioId } = useActivityStore()

  // Simulate receiving proactive alerts
  useEffect(() => {
    // Show alerts after a delay to simulate "proactive" detection
    const timer = setTimeout(() => {
      setAlerts(DEMO_ALERTS)
    }, 3000)

    return () => clearTimeout(timer)
  }, [])

  // Filter alerts relevant to selected portfolio
  const relevantAlerts = alerts.filter(
    (alert) =>
      !alert.dismissed &&
      (!selectedPortfolioId || alert.affectedPortfolios.includes(selectedPortfolioId))
  )

  const currentAlert = relevantAlerts[currentAlertIndex]

  const dismissAlert = (alertId: string) => {
    setAlerts((prev) =>
      prev.map((a) => (a.id === alertId ? { ...a, dismissed: true } : a))
    )
    if (currentAlertIndex >= relevantAlerts.length - 1) {
      setCurrentAlertIndex(Math.max(0, currentAlertIndex - 1))
    }
  }

  const handleAction = async (alert: ProactiveAlert) => {
    // Select first affected portfolio if none selected
    const portfolioId = selectedPortfolioId || alert.affectedPortfolios[0]

    if (!portfolioId) {
      dismissAlert(alert.id)
      return
    }

    // Set portfolio if not already selected
    if (!selectedPortfolioId && alert.affectedPortfolios[0]) {
      setSelectedPortfolioId(alert.affectedPortfolios[0])
    }

    setIsLoading(true)
    clearActivities()

    try {
      // Trigger the analysis via API
      const response = await fetch(`${API_URL}/api/events/inject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          event_type: alert.eventType || 'tech_crash',
          portfolio_id: portfolioId,
          magnitude: -0.04,
          enable_debate: true,
          enable_thinking: true,
          enable_chain_reaction: true,
        }),
      })

      if (response.ok) {
        dismissAlert(alert.id)
      }
    } catch (err) {
      console.error('Failed to trigger analysis:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const getSeverityStyles = (severity: string) => {
    switch (severity) {
      case 'critical':
        return {
          bg: 'bg-error/10',
          border: 'border-error/30',
          icon: 'text-error',
          badge: 'bg-error text-white',
        }
      case 'warning':
        return {
          bg: 'bg-warning/10',
          border: 'border-warning/30',
          icon: 'text-warning',
          badge: 'bg-warning text-black',
        }
      default:
        return {
          bg: 'bg-info/10',
          border: 'border-info/30',
          icon: 'text-info',
          badge: 'bg-info text-white',
        }
    }
  }

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'market_move':
        return TrendingDown
      case 'tax_deadline':
        return Clock
      case 'drift_detected':
        return AlertTriangle
      default:
        return Bell
    }
  }

  if (relevantAlerts.length === 0) {
    return null
  }

  const styles = getSeverityStyles(currentAlert.severity)
  const AlertIcon = getAlertIcon(currentAlert.type)

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        className={`mb-6 rounded-xl ${styles.bg} border ${styles.border} overflow-hidden`}
      >
        <div className="p-4">
          <div className="flex items-start gap-4">
            {/* Icon */}
            <div className={`p-2 rounded-lg ${styles.bg}`}>
              <AlertIcon className={`w-5 h-5 ${styles.icon}`} />
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${styles.badge}`}>
                  <Zap className="w-3 h-3 inline mr-1" />
                  Proactive Alert
                </span>
                <span className="text-xs text-text-muted">
                  {new Date(currentAlert.timestamp).toLocaleTimeString()}
                </span>
              </div>

              <h4 className="font-semibold text-text-primary mb-1">
                {currentAlert.title}
              </h4>
              <p className="text-sm text-text-secondary">
                {currentAlert.description}
              </p>

              {/* Affected portfolios */}
              <div className="flex items-center gap-2 mt-2">
                <span className="text-xs text-text-muted">Affects:</span>
                {currentAlert.affectedPortfolios.map((p) => (
                  <span
                    key={p}
                    className="text-xs px-2 py-0.5 bg-bg-tertiary rounded-full text-text-secondary"
                  >
                    {p.replace('_', ' ')}
                  </span>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2">
              {currentAlert.actionLabel && (
                <button
                  onClick={() => handleAction(currentAlert)}
                  disabled={isLoading}
                  className="btn-primary text-sm flex items-center gap-2"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      {currentAlert.actionLabel}
                      <ChevronRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              )}
              <button
                onClick={() => dismissAlert(currentAlert.id)}
                className="btn-ghost p-2"
                title="Dismiss"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Alert navigation (if multiple) */}
        {relevantAlerts.length > 1 && (
          <div className="px-4 py-2 bg-black/5 border-t border-white/5 flex items-center justify-between">
            <span className="text-xs text-text-muted">
              Alert {currentAlertIndex + 1} of {relevantAlerts.length}
            </span>
            <div className="flex gap-1">
              {relevantAlerts.map((_, idx) => (
                <button
                  key={idx}
                  onClick={() => setCurrentAlertIndex(idx)}
                  className={`w-2 h-2 rounded-full transition-colors ${
                    idx === currentAlertIndex ? 'bg-accent' : 'bg-text-muted/30'
                  }`}
                />
              ))}
            </div>
          </div>
        )}
      </motion.div>
    </AnimatePresence>
  )
}
