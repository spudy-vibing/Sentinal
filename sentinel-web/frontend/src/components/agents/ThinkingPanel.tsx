import { motion, AnimatePresence } from 'framer-motion'
import { Brain, Lightbulb, CheckCircle, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'
import { useActivityStore } from '../../stores/activityStore'
import AgentAvatar from './AgentAvatar'

interface ThinkingPanelProps {
  agentName?: string
  expanded?: boolean
}

export default function ThinkingPanel({ agentName, expanded = true }: ThinkingPanelProps) {
  const [isExpanded, setIsExpanded] = useState(expanded)
  const { thinkingStream } = useActivityStore()

  // Filter thinking streams
  const streams = agentName
    ? { [agentName]: thinkingStream[agentName] }
    : thinkingStream

  const hasActiveThinking = Object.keys(streams).some((k) => streams[k])

  if (!hasActiveThinking && !Object.keys(thinkingStream).length) {
    return null
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="card overflow-hidden"
    >
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-4 flex items-center justify-between hover:bg-bg-tertiary transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-accent/10 border border-accent/20">
            <Brain className="w-4 h-4 text-accent animate-pulse" />
          </div>
          <div className="text-left">
            <h3 className="font-medium text-text-primary">Agent Thinking</h3>
            <p className="text-xs text-text-muted">
              {Object.keys(streams).filter((k) => streams[k]).length} agent(s) active
            </p>
          </div>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-5 h-5 text-text-muted" />
        ) : (
          <ChevronDown className="w-5 h-5 text-text-muted" />
        )}
      </button>

      {/* Content */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-border-subtle"
          >
            <div className="p-4 space-y-4 max-h-96 overflow-y-auto">
              {Object.entries(streams).map(([agent, thought]) => {
                if (!thought) return null

                const agentType = agent.toLowerCase().includes('drift')
                  ? 'drift'
                  : agent.toLowerCase().includes('tax')
                  ? 'tax'
                  : agent.toLowerCase().includes('compliance')
                  ? 'compliance'
                  : agent.toLowerCase().includes('scenario')
                  ? 'scenario'
                  : 'coordinator'

                return (
                  <ThoughtStream
                    key={agent}
                    agentName={agent}
                    agentType={agentType}
                    thought={thought}
                  />
                )
              })}

              {Object.keys(streams).filter((k) => streams[k]).length === 0 && (
                <div className="text-center py-8">
                  <Lightbulb className="w-8 h-8 text-text-muted mx-auto mb-2 opacity-50" />
                  <p className="text-sm text-text-muted">No active thinking streams</p>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

interface ThoughtStreamProps {
  agentName: string
  agentType: 'coordinator' | 'drift' | 'tax' | 'compliance' | 'scenario'
  thought: string
}

function ThoughtStream({ agentName, agentType, thought }: ThoughtStreamProps) {
  const lines = thought.split('\n').filter(Boolean)

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      className="p-4 rounded-lg bg-bg-tertiary border border-border-subtle"
    >
      {/* Agent Header */}
      <div className="flex items-center gap-3 mb-3">
        <AgentAvatar type={agentType} size="sm" isActive isThinking />
        <span className="font-medium text-text-primary">{agentName}</span>
      </div>

      {/* Thought Content */}
      <div className="pl-11 space-y-2">
        {lines.map((line, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: idx * 0.1 }}
            className="flex items-start gap-2"
          >
            <ThoughtIcon index={idx} total={lines.length} />
            <p className="text-sm text-text-secondary font-mono">{line}</p>
          </motion.div>
        ))}

        {/* Typing cursor */}
        <div className="flex items-center gap-2">
          <span className="w-2 h-4 bg-accent animate-pulse rounded-sm" />
        </div>
      </div>
    </motion.div>
  )
}

function ThoughtIcon({ index, total }: { index: number; total: number }) {
  // First line = hypothesis, last = conclusion, middle = analysis
  if (index === 0) {
    return <Lightbulb className="w-3 h-3 text-warning mt-1 flex-shrink-0" />
  }
  if (index === total - 1) {
    return <CheckCircle className="w-3 h-3 text-success mt-1 flex-shrink-0" />
  }
  return <Brain className="w-3 h-3 text-accent mt-1 flex-shrink-0" />
}

// Compact version for inline display
export function ThinkingIndicator({ agentName }: { agentName: string }) {
  const { thinkingStream } = useActivityStore()
  const thought = thinkingStream[agentName]

  if (!thought) return null

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      className="mt-2 p-2 rounded bg-accent/5 border border-accent/20"
    >
      <div className="flex items-center gap-2 mb-1">
        <Brain className="w-3 h-3 text-accent animate-pulse" />
        <span className="text-xs text-accent">Thinking...</span>
      </div>
      <p className="text-xs text-text-secondary font-mono line-clamp-2">
        {thought}
        <span className="inline-block w-1.5 h-3 bg-accent animate-pulse ml-0.5" />
      </p>
    </motion.div>
  )
}
