import { motion } from 'framer-motion'
import { Check, Loader2, Circle } from 'lucide-react'
import { useActivityStore } from '../stores/activityStore'

type State = 'MONITOR' | 'DETECT' | 'ANALYZE' | 'CONFLICT' | 'RECOMMEND' | 'REVIEW' | 'APPROVED'

interface StateConfig {
  label: string
  shortLabel: string
}

const STATES: Record<State, StateConfig> = {
  MONITOR: { label: 'Monitoring', shortLabel: 'MON' },
  DETECT: { label: 'Event Detected', shortLabel: 'DET' },
  ANALYZE: { label: 'Analyzing', shortLabel: 'ANL' },
  CONFLICT: { label: 'Resolving Conflict', shortLabel: 'CFT' },
  RECOMMEND: { label: 'Recommending', shortLabel: 'REC' },
  REVIEW: { label: 'Awaiting Review', shortLabel: 'REV' },
  APPROVED: { label: 'Approved', shortLabel: 'APR' },
}

const STATE_ORDER: State[] = ['MONITOR', 'DETECT', 'ANALYZE', 'CONFLICT', 'RECOMMEND', 'REVIEW', 'APPROVED']

export default function StateMachineIndicator() {
  const { activities, activeAgents, debatePhase, scenarios, completedAgents } = useActivityStore()

  // Derive current state from activity
  const getCurrentState = (): State => {
    // Check for approved scenarios
    const hasApproved = activities.some(a => a.status === 'approved')
    if (hasApproved) return 'APPROVED'

    // Check for scenarios awaiting review
    if (scenarios.length > 0) return 'REVIEW'

    // Check for debate/conflict resolution
    if (debatePhase) return 'CONFLICT'

    // Check for active analysis
    if (activeAgents.length > 0 || completedAgents.length > 0) return 'ANALYZE'

    // Check for detection
    const hasGateway = activities.some(a => a.agent_type === 'gateway')
    if (hasGateway) return 'DETECT'

    return 'MONITOR'
  }

  const currentState = getCurrentState()
  const currentIndex = STATE_ORDER.indexOf(currentState)

  return (
    <div className="flex items-center gap-1 overflow-x-auto scrollbar-hide py-2">
      {STATE_ORDER.map((state, index) => {
        const isComplete = index < currentIndex
        const isCurrent = index === currentIndex
        // isPending = index > currentIndex (used implicitly in else branch)

        return (
          <motion.div
            key={state}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.05 }}
            className="flex items-center"
          >
            {/* State Node */}
            <div
              className={`
                relative flex items-center justify-center w-8 h-8 rounded-full text-xs font-medium
                transition-all duration-300
                ${isComplete
                  ? 'bg-success text-white'
                  : isCurrent
                    ? 'bg-accent text-white shadow-glow'
                    : 'bg-bg-tertiary text-text-muted border border-border-subtle'
                }
              `}
            >
              {isComplete ? (
                <Check className="w-4 h-4" />
              ) : isCurrent ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Circle className="w-3 h-3" />
              )}

              {/* Tooltip */}
              <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 whitespace-nowrap">
                <span
                  className={`text-[10px] ${
                    isCurrent ? 'text-accent font-medium' : 'text-text-muted'
                  }`}
                >
                  {STATES[state].shortLabel}
                </span>
              </div>

              {/* Pulse ring for current state */}
              {isCurrent && (
                <div className="absolute inset-0 rounded-full border-2 border-accent animate-ping opacity-30" />
              )}
            </div>

            {/* Connector Line */}
            {index < STATE_ORDER.length - 1 && (
              <div
                className={`
                  w-4 h-0.5 mx-0.5
                  ${isComplete ? 'bg-success' : 'bg-border-subtle'}
                `}
              />
            )}
          </motion.div>
        )
      })}
    </div>
  )
}

// Compact version for header
export function StateMachineCompact() {
  const { activities, activeAgents, debatePhase, scenarios, completedAgents } = useActivityStore()

  const getCurrentState = (): State => {
    const hasApproved = activities.some(a => a.status === 'approved')
    if (hasApproved) return 'APPROVED'
    if (scenarios.length > 0) return 'REVIEW'
    if (debatePhase) return 'CONFLICT'
    if (activeAgents.length > 0 || completedAgents.length > 0) return 'ANALYZE'
    const hasGateway = activities.some(a => a.agent_type === 'gateway')
    if (hasGateway) return 'DETECT'
    return 'MONITOR'
  }

  const currentState = getCurrentState()
  const config = STATES[currentState]

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-bg-tertiary border border-border-subtle">
      {currentState !== 'MONITOR' ? (
        <Loader2 className="w-3.5 h-3.5 text-accent animate-spin" />
      ) : (
        <div className="w-2 h-2 rounded-full bg-success" />
      )}
      <span className="text-xs font-medium text-text-secondary">
        {config.label}
      </span>
    </div>
  )
}
