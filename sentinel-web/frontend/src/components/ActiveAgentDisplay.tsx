import { motion, AnimatePresence } from 'framer-motion'
import { Brain, Loader2, CheckCircle2, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'
import { useActivityStore } from '../stores/activityStore'

export default function ActiveAgentDisplay() {
  const { activeAgents, thinkingStream, completedAgents } = useActivityStore()
  const [expandedAgent, setExpandedAgent] = useState<string | null>(null)

  // Get the agent that's currently thinking
  const thinkingAgents = Object.entries(thinkingStream)
  const hasActivity = thinkingAgents.length > 0 || activeAgents.length > 0 || completedAgents.length > 0

  if (!hasActivity) {
    return null
  }

  return (
    <div className="space-y-3">
      <AnimatePresence mode="popLayout">
        {thinkingAgents.map(([agentName, state]) => (
          <motion.div
            key={agentName}
            initial={{ opacity: 0, y: -20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -20, scale: 0.95 }}
            className="relative overflow-hidden rounded-xl border-2 border-accent bg-gradient-to-br from-accent/5 to-accent/10"
          >
            {/* Animated background pulse */}
            <div className="absolute inset-0 bg-accent/5 animate-pulse" />

            {/* Content */}
            <div className="relative p-4">
              {/* Header */}
              <div className="flex items-center gap-3 mb-3">
                <div className="relative">
                  <div className="w-10 h-10 rounded-full bg-accent/20 flex items-center justify-center">
                    <Brain className="w-5 h-5 text-accent" />
                  </div>
                  {/* Pulsing ring */}
                  <div className="absolute inset-0 rounded-full border-2 border-accent animate-ping opacity-30" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-text-primary">{agentName}</span>
                    <span className="px-2 py-0.5 text-xs font-medium bg-accent text-white rounded-full">
                      Analyzing
                    </span>
                  </div>
                  <span className="text-xs text-text-muted">Processing market event...</span>
                </div>
                <Loader2 className="w-5 h-5 text-accent animate-spin" />
              </div>

              {/* Thinking Stream */}
              <div className="bg-white/50 rounded-lg p-3 border border-accent/20">
                <div className="flex items-start gap-2">
                  <span className="text-accent font-bold text-lg leading-none mt-0.5">›</span>
                  <div className="flex-1 min-w-0">
                    <AnimatePresence mode="wait">
                      <motion.p
                        key={state.text}
                        initial={{ opacity: 0, y: 5 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -5 }}
                        className="text-sm text-text-primary font-medium leading-relaxed"
                      >
                        {state.text || 'Initializing analysis...'}
                      </motion.p>
                    </AnimatePresence>

                    {/* Previous thoughts (faded) */}
                    {state.thoughts.length > 1 && (
                      <div className="mt-2 pt-2 border-t border-accent/10 space-y-1">
                        {state.thoughts.slice(-3, -1).map((thought, idx) => (
                          <p key={idx} className="text-xs text-text-muted truncate">
                            {thought}
                          </p>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Bottom progress indicator */}
            <div className="h-1 bg-accent/20">
              <motion.div
                className="h-full bg-accent"
                initial={{ width: '0%' }}
                animate={{ width: '100%' }}
                transition={{ duration: 8, ease: 'linear', repeat: Infinity }}
              />
            </div>
          </motion.div>
        ))}
      </AnimatePresence>

      {/* Show active agents without thinking as smaller cards */}
      {activeAgents
        .filter(agent => !thinkingStream[agent.name])
        .map(agent => (
          <motion.div
            key={agent.name}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center gap-3 p-3 rounded-lg bg-bg-tertiary border border-border-subtle"
          >
            <div className="w-2 h-2 rounded-full bg-accent animate-pulse" />
            <span className="text-sm font-medium text-text-primary">{agent.name}</span>
            <span className="text-xs text-text-muted">Starting analysis...</span>
          </motion.div>
        ))}

      {/* Completed Agents Summary */}
      {completedAgents.length > 0 && thinkingAgents.length === 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl border border-success/30 bg-success/5 overflow-hidden"
        >
          <div className="p-4 border-b border-success/20">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-success" />
              <span className="font-semibold text-text-primary">Analysis Complete</span>
              <span className="text-xs text-text-muted ml-auto">
                {completedAgents.length} agents finished
              </span>
            </div>
          </div>
          <div className="divide-y divide-success/10">
            {completedAgents.map((agent) => (
              <div key={agent.name} className="p-3">
                <button
                  onClick={() => setExpandedAgent(expandedAgent === agent.name ? null : agent.name)}
                  className="w-full text-left"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-success" />
                      <span className="text-sm font-medium text-text-primary">{agent.name}</span>
                    </div>
                    {agent.thoughts.length > 0 && (
                      expandedAgent === agent.name ?
                        <ChevronUp className="w-4 h-4 text-text-muted" /> :
                        <ChevronDown className="w-4 h-4 text-text-muted" />
                    )}
                  </div>
                  <p className="text-xs text-text-secondary mt-1 ml-4">{agent.summary}</p>
                </button>

                {/* Expanded thinking history */}
                <AnimatePresence>
                  {expandedAgent === agent.name && agent.thoughts.length > 0 && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="mt-2 ml-4 pl-3 border-l-2 border-success/30 space-y-1 overflow-hidden"
                    >
                      {agent.thoughts.map((thought, idx) => (
                        <p key={idx} className="text-xs text-text-muted">
                          <span className="text-success mr-1">›</span>
                          {thought}
                        </p>
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  )
}
