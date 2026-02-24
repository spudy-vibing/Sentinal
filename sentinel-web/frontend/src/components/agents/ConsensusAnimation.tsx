import { motion } from 'framer-motion'
import { Check, Handshake, Sparkles } from 'lucide-react'
import AgentAvatar from './AgentAvatar'

interface ConsensusAnimationProps {
  agents: Array<{
    name: string
    type: 'drift' | 'tax' | 'compliance' | 'scenario' | 'coordinator'
    agreed: boolean
  }>
  consensus: string
  isComplete: boolean
}

export default function ConsensusAnimation({
  agents,
  consensus,
  isComplete,
}: ConsensusAnimationProps) {
  const agreedCount = agents.filter((a) => a.agreed).length
  const progress = (agreedCount / agents.length) * 100

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="card p-6 overflow-hidden"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <motion.div
            animate={isComplete ? { rotate: [0, 10, -10, 0] } : {}}
            transition={{ duration: 0.5 }}
            className={`p-2 rounded-lg ${
              isComplete
                ? 'bg-success/10 border border-success/30'
                : 'bg-accent/10 border border-accent/30'
            }`}
          >
            {isComplete ? (
              <Handshake className="w-5 h-5 text-success" />
            ) : (
              <Sparkles className="w-5 h-5 text-accent animate-pulse" />
            )}
          </motion.div>
          <div>
            <h3 className="font-medium text-text-primary">
              {isComplete ? 'Consensus Reached' : 'Building Consensus'}
            </h3>
            <p className="text-xs text-text-muted">
              {agreedCount} of {agents.length} agents agreed
            </p>
          </div>
        </div>

        <div className="text-right">
          <span
            className={`text-2xl font-bold ${
              isComplete ? 'text-success' : 'text-accent'
            }`}
          >
            {Math.round(progress)}%
          </span>
        </div>
      </div>

      {/* Progress bar */}
      <div className="h-2 bg-bg-tertiary rounded-full overflow-hidden mb-6">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
          className={`h-full rounded-full ${
            isComplete
              ? 'bg-gradient-to-r from-success to-success/70'
              : 'bg-gradient-to-r from-accent to-accent/70'
          }`}
        />
      </div>

      {/* Agent votes */}
      <div className="grid grid-cols-2 gap-3 mb-6">
        {agents.map((agent, index) => (
          <motion.div
            key={agent.name}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className={`flex items-center gap-3 p-3 rounded-lg border ${
              agent.agreed
                ? 'bg-success/5 border-success/30'
                : 'bg-bg-tertiary border-border-subtle'
            }`}
          >
            <AgentAvatar
              type={agent.type}
              size="sm"
              isActive={!agent.agreed}
              showPulse={!agent.agreed}
            />
            <div className="flex-1">
              <p className="text-sm font-medium text-text-primary">
                {agent.name}
              </p>
            </div>
            {agent.agreed ? (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', stiffness: 500, damping: 25 }}
              >
                <Check className="w-5 h-5 text-success" />
              </motion.div>
            ) : (
              <div className="w-5 h-5 rounded-full border-2 border-text-muted border-dashed" />
            )}
          </motion.div>
        ))}
      </div>

      {/* Consensus statement */}
      {isComplete && consensus && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="p-4 rounded-lg bg-success/5 border border-success/30"
        >
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="w-4 h-4 text-success" />
            <span className="text-sm font-medium text-success">
              Final Recommendation
            </span>
          </div>
          <p className="text-text-primary">{consensus}</p>
        </motion.div>
      )}

      {/* Animated connecting lines (background effect) */}
      <svg
        className="absolute inset-0 w-full h-full pointer-events-none opacity-10"
        style={{ zIndex: -1 }}
      >
        {isComplete && (
          <motion.circle
            cx="50%"
            cy="50%"
            r="30%"
            fill="none"
            stroke="currentColor"
            strokeWidth="1"
            className="text-success"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 0.5 }}
            transition={{ duration: 1 }}
          />
        )}
      </svg>
    </motion.div>
  )
}

// Mini version for inline use
export function ConsensusIndicator({
  progress,
  isComplete,
}: {
  progress: number
  isComplete: boolean
}) {
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-1.5 bg-bg-tertiary rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          className={`h-full rounded-full ${
            isComplete ? 'bg-success' : 'bg-accent'
          }`}
        />
      </div>
      <span
        className={`text-xs font-medium ${
          isComplete ? 'text-success' : 'text-accent'
        }`}
      >
        {Math.round(progress)}%
      </span>
      {isComplete && <Check className="w-3 h-3 text-success" />}
    </div>
  )
}
