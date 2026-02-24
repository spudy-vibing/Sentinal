import { motion, AnimatePresence } from 'framer-motion'
import { Check, Loader2, AlertTriangle, Brain, Clock } from 'lucide-react'

type AgentType = 'coordinator' | 'drift' | 'tax' | 'compliance' | 'scenario'
type AgentState = 'idle' | 'analyzing' | 'thinking' | 'debating' | 'complete' | 'error'

interface AgentNodeProps {
  id: string
  name: string
  description: string
  type: AgentType
  state: AgentState
  message: string | null
  thinking: string | null
  delay?: number
}

const TYPE_COLORS: Record<AgentType, { border: string; bg: string; text: string }> = {
  coordinator: {
    border: 'border-text-primary/30',
    bg: 'bg-text-primary/10',
    text: 'text-text-primary',
  },
  drift: {
    border: 'border-info/30',
    bg: 'bg-info/10',
    text: 'text-info',
  },
  tax: {
    border: 'border-success/30',
    bg: 'bg-success/10',
    text: 'text-success',
  },
  compliance: {
    border: 'border-warning/30',
    bg: 'bg-warning/10',
    text: 'text-warning',
  },
  scenario: {
    border: 'border-accent/30',
    bg: 'bg-accent/10',
    text: 'text-accent',
  },
}

export default function AgentNode({
  id,
  name,
  description,
  type,
  state,
  message,
  thinking,
  delay = 0,
}: AgentNodeProps) {
  const colors = TYPE_COLORS[type]
  const isActive = state === 'analyzing' || state === 'thinking' || state === 'debating'

  const getStateIcon = () => {
    switch (state) {
      case 'analyzing':
        return <Loader2 className="w-4 h-4 animate-spin" />
      case 'thinking':
        return <Brain className="w-4 h-4 animate-pulse" />
      case 'debating':
        return <Brain className="w-4 h-4 animate-pulse" />
      case 'complete':
        return <Check className="w-4 h-4" />
      case 'error':
        return <AlertTriangle className="w-4 h-4" />
      default:
        return <Clock className="w-4 h-4 opacity-50" />
    }
  }

  const getStateColor = () => {
    switch (state) {
      case 'analyzing':
      case 'thinking':
      case 'debating':
        return 'text-accent'
      case 'complete':
        return 'text-success'
      case 'error':
        return 'text-error'
      default:
        return 'text-text-muted'
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay, duration: 0.3 }}
      className="relative pl-14"
    >
      {/* Node indicator */}
      <motion.div
        animate={{
          scale: isActive ? [1, 1.2, 1] : 1,
          boxShadow: isActive
            ? ['0 0 0 rgba(0,229,204,0)', '0 0 20px rgba(0,229,204,0.3)', '0 0 0 rgba(0,229,204,0)']
            : 'none',
        }}
        transition={{
          duration: 1.5,
          repeat: isActive ? Infinity : 0,
          ease: 'easeInOut',
        }}
        className={`absolute left-4 top-4 w-4 h-4 rounded-full border-2 ${
          isActive
            ? 'bg-accent border-accent'
            : state === 'complete'
            ? 'bg-success border-success'
            : 'bg-bg-tertiary border-border-default'
        }`}
      />

      {/* Card */}
      <motion.div
        animate={{
          borderColor: isActive ? 'rgba(0, 229, 204, 0.3)' : undefined,
        }}
        className={`p-4 rounded-lg border transition-all duration-300 ${
          isActive
            ? 'bg-accent/5 border-accent/30 shadow-glow'
            : state === 'complete'
            ? `${colors.bg} ${colors.border}`
            : 'bg-bg-tertiary border-border-subtle'
        }`}
      >
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            <span className={`font-medium ${isActive ? 'text-accent' : colors.text}`}>
              {name}
            </span>
            <span className="text-xs text-text-muted">{description}</span>
          </div>
          <div className={getStateColor()}>{getStateIcon()}</div>
        </div>

        {/* Message */}
        <AnimatePresence mode="wait">
          {(message || thinking) && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-2"
            >
              {thinking ? (
                <div className="p-2 bg-bg-secondary rounded border border-border-subtle">
                  <div className="flex items-center gap-2 mb-1">
                    <Brain className="w-3 h-3 text-accent animate-pulse" />
                    <span className="text-xs text-accent">Thinking...</span>
                  </div>
                  <p className="text-sm text-text-secondary font-mono">
                    {thinking}
                    <span className="inline-block w-2 h-3 bg-accent animate-pulse ml-0.5" />
                  </p>
                </div>
              ) : (
                <p className="text-sm text-text-secondary">{message}</p>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </motion.div>
  )
}
