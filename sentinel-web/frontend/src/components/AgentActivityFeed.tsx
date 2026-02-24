import { motion, AnimatePresence } from 'framer-motion'
import { Activity, Brain, AlertTriangle, Check, Clock, Loader2 } from 'lucide-react'
import { useActivityStore } from '../stores/activityStore'

export default function AgentActivityFeed() {
  const { activities, thinkingStream } = useActivityStore()

  // Show most recent activities first, limit to reasonable amount
  const displayActivities = activities.slice(-20).reverse()
  const hasThinking = Object.keys(thinkingStream).length > 0

  return (
    <div className="card h-full flex flex-col max-h-[600px]">
      <div className="p-4 border-b border-border-subtle flex items-center justify-between">
        <h3 className="font-medium text-text-primary flex items-center gap-2">
          <Activity className="w-4 h-4 text-accent" />
          Agent Activity
        </h3>
        <span className="text-xs text-text-muted">
          {displayActivities.length} events
        </span>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {/* Thinking Stream - Now shows individual thoughts cleanly */}
        <AnimatePresence mode="popLayout">
          {Object.entries(thinkingStream).map(([agentName, state]) => (
            <motion.div
              key={agentName}
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10, height: 0 }}
              className="p-3 bg-accent/5 border border-accent/20 rounded-lg"
            >
              <div className="flex items-center gap-2 mb-2">
                <Loader2 className="w-4 h-4 text-accent animate-spin" />
                <span className="text-sm font-medium text-accent">{agentName}</span>
                <span className="text-xs text-text-muted">analyzing...</span>
              </div>

              {/* Show latest thought with proper formatting */}
              <div className="space-y-1">
                {state.thoughts.slice(-3).map((thought, idx) => (
                  <motion.p
                    key={idx}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: idx === state.thoughts.length - 1 ? 1 : 0.5 }}
                    className={`text-sm font-mono ${
                      idx === state.thoughts.slice(-3).length - 1
                        ? 'text-text-primary'
                        : 'text-text-muted text-xs'
                    }`}
                  >
                    {idx === state.thoughts.slice(-3).length - 1 && (
                      <span className="text-accent mr-1">›</span>
                    )}
                    {thought}
                  </motion.p>
                ))}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Activity Log - Most recent first */}
        <AnimatePresence mode="popLayout">
          {displayActivities.map((activity) => (
            <motion.div
              key={activity.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              layout
              className={`p-3 rounded-lg border-l-2 ${getAgentBorderColor(activity.agent_type)}`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium text-text-primary">
                  {activity.agent_name}
                </span>
                {getStatusIcon(activity.status)}
              </div>
              <p className="text-sm text-text-secondary line-clamp-2">{activity.message}</p>
              <span className="text-xs text-text-muted">
                {formatTime(activity.timestamp)}
              </span>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Empty State */}
        {displayActivities.length === 0 && !hasThinking && (
          <div className="text-center py-8">
            <Activity className="w-8 h-8 text-text-muted mx-auto mb-2" />
            <p className="text-sm text-text-muted">No recent activity</p>
            <p className="text-xs text-text-muted">Inject an event to see agents in action</p>
          </div>
        )}
      </div>
    </div>
  )
}

function getAgentBorderColor(agentType: string): string {
  switch (agentType) {
    case 'drift':
      return 'border-info bg-info/5'
    case 'tax':
      return 'border-success bg-success/5'
    case 'compliance':
      return 'border-warning bg-warning/5'
    case 'scenario':
    case 'coordinator':
      return 'border-accent bg-accent/5'
    case 'gateway':
      return 'border-border-default bg-bg-tertiary'
    default:
      return 'border-border-subtle bg-bg-tertiary'
  }
}

function getStatusIcon(status: string) {
  switch (status) {
    case 'complete':
      return <Check className="w-4 h-4 text-success" />
    case 'active':
    case 'analyzing':
    case 'thinking':
      return <Loader2 className="w-4 h-4 text-accent animate-spin" />
    case 'warning':
      return <AlertTriangle className="w-4 h-4 text-warning" />
    case 'error':
      return <AlertTriangle className="w-4 h-4 text-error" />
    default:
      return <Clock className="w-4 h-4 text-text-muted" />
  }
}

function formatTime(timestamp: string): string {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  if (isNaN(date.getTime())) return ''
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}
