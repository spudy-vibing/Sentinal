import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Bell,
  AlertTriangle,
  AlertCircle,
  Info,
  X,
  Check,
  ChevronRight,
  Clock,
} from 'lucide-react'
import AgentAvatar from '../agents/AgentAvatar'

export interface Alert {
  id: string
  agent_name: string
  agent_type: 'drift' | 'tax' | 'compliance' | 'scenario' | 'coordinator'
  severity: 'info' | 'warning' | 'critical'
  title: string
  description: string
  portfolio_id: string
  suggested_action?: string
  timestamp: string
  acknowledged: boolean
}

interface AlertPanelProps {
  alerts: Alert[]
  onAcknowledge: (alertId: string) => void
  onDismiss: (alertId: string) => void
  onAction: (alert: Alert) => void
}

export default function AlertPanel({
  alerts,
  onAcknowledge,
  onDismiss,
  onAction,
}: AlertPanelProps) {
  const [filter, setFilter] = useState<'all' | 'unread'>('unread')

  const filteredAlerts =
    filter === 'unread' ? alerts.filter((a) => !a.acknowledged) : alerts

  const criticalCount = alerts.filter(
    (a) => a.severity === 'critical' && !a.acknowledged
  ).length

  return (
    <div className="card overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-border-subtle flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="relative">
            <Bell className="w-5 h-5 text-text-primary" />
            {criticalCount > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-error text-[10px] font-bold text-white flex items-center justify-center">
                {criticalCount}
              </span>
            )}
          </div>
          <div>
            <h3 className="font-medium text-text-primary">Proactive Alerts</h3>
            <p className="text-xs text-text-muted">
              {filteredAlerts.length} alert{filteredAlerts.length !== 1 ? 's' : ''}
            </p>
          </div>
        </div>

        <div className="flex gap-1">
          <button
            onClick={() => setFilter('unread')}
            className={`px-3 py-1 text-xs rounded-md transition-colors ${
              filter === 'unread'
                ? 'bg-accent/10 text-accent'
                : 'text-text-muted hover:bg-bg-tertiary'
            }`}
          >
            Unread
          </button>
          <button
            onClick={() => setFilter('all')}
            className={`px-3 py-1 text-xs rounded-md transition-colors ${
              filter === 'all'
                ? 'bg-accent/10 text-accent'
                : 'text-text-muted hover:bg-bg-tertiary'
            }`}
          >
            All
          </button>
        </div>
      </div>

      {/* Alerts List */}
      <div className="max-h-96 overflow-y-auto">
        <AnimatePresence mode="popLayout">
          {filteredAlerts.length === 0 ? (
            <div className="p-8 text-center">
              <Bell className="w-8 h-8 text-text-muted mx-auto mb-2 opacity-50" />
              <p className="text-sm text-text-muted">No alerts</p>
              <p className="text-xs text-text-muted">
                Agents will notify you of important events
              </p>
            </div>
          ) : (
            filteredAlerts.map((alert) => (
              <AlertItem
                key={alert.id}
                alert={alert}
                onAcknowledge={() => onAcknowledge(alert.id)}
                onDismiss={() => onDismiss(alert.id)}
                onAction={() => onAction(alert)}
              />
            ))
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

interface AlertItemProps {
  alert: Alert
  onAcknowledge: () => void
  onDismiss: () => void
  onAction: () => void
}

function AlertItem({ alert, onAcknowledge, onDismiss, onAction }: AlertItemProps) {
  const severityConfig = {
    info: {
      icon: Info,
      color: 'text-info',
      bg: 'bg-info/5',
      border: 'border-info/20',
    },
    warning: {
      icon: AlertTriangle,
      color: 'text-warning',
      bg: 'bg-warning/5',
      border: 'border-warning/20',
    },
    critical: {
      icon: AlertCircle,
      color: 'text-error',
      bg: 'bg-error/5',
      border: 'border-error/20',
    },
  }

  const config = severityConfig[alert.severity]
  const SeverityIcon = config.icon

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      className={`p-4 border-b border-border-subtle ${
        alert.acknowledged ? 'opacity-60' : ''
      } hover:bg-bg-tertiary/50 transition-colors`}
    >
      <div className="flex items-start gap-3">
        {/* Severity Icon */}
        <div className={`p-2 rounded-lg ${config.bg} border ${config.border}`}>
          <SeverityIcon className={`w-4 h-4 ${config.color}`} />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-sm font-medium ${config.color}`}>
              {alert.title}
            </span>
            {!alert.acknowledged && (
              <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
            )}
          </div>

          <p className="text-sm text-text-secondary mb-2">{alert.description}</p>

          {/* Agent & Time */}
          <div className="flex items-center gap-3 mb-2">
            <div className="flex items-center gap-1.5">
              <AgentAvatar type={alert.agent_type} size="sm" />
              <span className="text-xs text-text-muted">{alert.agent_name}</span>
            </div>
            <div className="flex items-center gap-1 text-xs text-text-muted">
              <Clock className="w-3 h-3" />
              {formatTime(alert.timestamp)}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            {alert.suggested_action && (
              <button
                onClick={onAction}
                className="flex items-center gap-1 px-2 py-1 text-xs bg-accent/10 text-accent rounded hover:bg-accent/20 transition-colors"
              >
                {alert.suggested_action}
                <ChevronRight className="w-3 h-3" />
              </button>
            )}

            {!alert.acknowledged && (
              <button
                onClick={onAcknowledge}
                className="flex items-center gap-1 px-2 py-1 text-xs text-text-muted hover:text-text-primary hover:bg-bg-tertiary rounded transition-colors"
              >
                <Check className="w-3 h-3" />
                Acknowledge
              </button>
            )}

            <button
              onClick={onDismiss}
              className="p-1 text-text-muted hover:text-text-primary hover:bg-bg-tertiary rounded transition-colors"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

function formatTime(timestamp: string): string {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`
  return date.toLocaleDateString()
}

// Export a toast version for popup alerts
export function AlertToast({ alert, onClose }: { alert: Alert; onClose: () => void }) {
  const severityConfig = {
    info: { icon: Info, color: 'text-info', border: 'border-info/30' },
    warning: { icon: AlertTriangle, color: 'text-warning', border: 'border-warning/30' },
    critical: { icon: AlertCircle, color: 'text-error', border: 'border-error/30' },
  }

  const config = severityConfig[alert.severity]
  const SeverityIcon = config.icon

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, x: 20 }}
      animate={{ opacity: 1, y: 0, x: 0 }}
      exit={{ opacity: 0, x: 100 }}
      className={`flex items-start gap-3 p-4 rounded-lg bg-bg-elevated border ${config.border} shadow-card-hover max-w-sm`}
    >
      <SeverityIcon className={`w-5 h-5 ${config.color} flex-shrink-0`} />
      <div className="flex-1 min-w-0">
        <p className={`text-sm font-medium ${config.color}`}>{alert.title}</p>
        <p className="text-xs text-text-secondary mt-0.5 line-clamp-2">
          {alert.description}
        </p>
      </div>
      <button onClick={onClose} className="p-1 hover:bg-bg-tertiary rounded">
        <X className="w-4 h-4 text-text-muted" />
      </button>
    </motion.div>
  )
}
