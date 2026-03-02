import { motion, AnimatePresence } from 'framer-motion'
import { MessageSquare, Scale, CheckCircle2, AlertTriangle, Users, Sparkles } from 'lucide-react'
import { useActivityStore } from '../stores/activityStore'

interface DebateMessageType {
  agent_id?: string
  agent_name: string
  phase?: string
  position: string
  message?: string
  argument?: string
  confidence: number
  key_points?: string[]
  timestamp?: string
}

export default function DebateDisplay() {
  const { debateMessages, debatePhase, debateQuestion, debateConsensus } = useActivityStore()

  if (!debatePhase && debateMessages.length === 0) {
    return null
  }

  const getPhaseLabel = (phase: string | null) => {
    switch (phase) {
      case 'opening':
        return 'Opening Arguments'
      case 'rebuttal':
        return 'Rebuttals'
      case 'synthesis':
        return 'Synthesis'
      case 'consensus':
        return 'Consensus Reached'
      default:
        return 'Debate in Progress'
    }
  }

  const getPositionStyle = (position: string) => {
    switch (position) {
      case 'for':
        return 'border-l-success bg-success/5'
      case 'against':
        return 'border-l-error bg-error/5'
      case 'neutral':
        return 'border-l-info bg-info/5'
      default:
        return 'border-l-accent bg-accent/5'
    }
  }

  const getAgentColor = (agentId: string) => {
    switch (agentId) {
      case 'drift':
        return 'text-info'
      case 'tax':
        return 'text-warning'
      case 'compliance':
        return 'text-error'
      case 'coordinator':
        return 'text-accent'
      default:
        return 'text-text-primary'
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="card"
    >
      {/* Header */}
      <div className="p-4 border-b border-border-subtle">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-warning/10">
              <Scale className="w-4 h-4 text-warning" />
            </div>
            <div>
              <h3 className="font-semibold text-text-primary">Agent Debate</h3>
              <p className="text-xs text-text-muted">{debateQuestion || 'Agents resolving conflict...'}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {debatePhase === 'consensus' ? (
              <span className="px-2.5 py-1 text-xs font-medium bg-success/10 text-success rounded-full flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" />
                Consensus
              </span>
            ) : (
              <span className="px-2.5 py-1 text-xs font-medium bg-warning/10 text-warning rounded-full flex items-center gap-1">
                <Users className="w-3 h-3" />
                {getPhaseLabel(debatePhase)}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Debate Messages */}
      <div className="p-4 space-y-3 max-h-80 overflow-y-auto">
        <AnimatePresence mode="popLayout">
          {(debateMessages as DebateMessageType[]).map((message, index) => (
            <motion.div
              key={`${message.agent_name}-${index}`}
              initial={{ opacity: 0, x: -20, scale: 0.95 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              transition={{ delay: index * 0.1 }}
              className={`p-3 rounded-lg border-l-4 ${getPositionStyle(message.position)}`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <MessageSquare className={`w-4 h-4 ${getAgentColor(message.agent_id || '')}`} />
                  <span className={`font-medium text-sm ${getAgentColor(message.agent_id || '')}`}>
                    {message.agent_name}
                  </span>
                  <span className={`text-xs px-1.5 py-0.5 rounded ${
                    message.position === 'for' ? 'bg-success/20 text-success' :
                    message.position === 'against' ? 'bg-error/20 text-error' :
                    'bg-info/20 text-info'
                  }`}>
                    {message.position}
                  </span>
                </div>
                <span className="text-xs text-text-muted">
                  {message.confidence}% confident
                </span>
              </div>

              <p className="text-sm text-text-primary leading-relaxed">
                {message.message || message.argument}
              </p>

              {/* Key Points */}
              {message.key_points && message.key_points.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {message.key_points.map((point: string, idx: number) => (
                    <span
                      key={idx}
                      className="text-xs px-2 py-0.5 bg-bg-tertiary text-text-secondary rounded"
                    >
                      {point}
                    </span>
                  ))}
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        {debateMessages.length === 0 && (
          <div className="text-center py-6">
            <AlertTriangle className="w-8 h-8 text-warning mx-auto mb-2 animate-pulse" />
            <p className="text-sm text-text-muted">Conflict detected - agents preparing arguments...</p>
          </div>
        )}
      </div>

      {/* Consensus & Final Recommendation */}
      {debatePhase === 'consensus' && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="border-t border-success/20"
        >
          {/* Consensus Banner */}
          <div className="p-3 bg-success/5 border-b border-success/10">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-success" />
              <p className="text-sm text-success font-medium">
                Agents have reached consensus on the recommended action
              </p>
            </div>
          </div>

          {/* Final Recommendation Card */}
          <div className="p-4">
            <div className="rounded-xl bg-gradient-to-br from-accent/10 via-accent/5 to-transparent border-2 border-accent/30 p-4">
              <div className="flex items-start gap-4">
                <div className="p-3 rounded-xl bg-accent/20 shrink-0">
                  <Sparkles className="w-6 h-6 text-accent" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    <h4 className="font-semibold text-text-primary">Final Recommendation</h4>
                    <span className="px-2 py-0.5 text-xs font-medium bg-accent text-white rounded-full">
                      AI Consensus
                    </span>
                  </div>

                  <p className="text-sm text-text-secondary mb-3">
                    {debateConsensus?.final_decision ||
                      (debateMessages.filter(m => m.phase === 'synthesis')[0]?.message) ||
                      'Based on the multi-agent analysis and debate, agents have reached consensus.'}
                  </p>

                  {/* Key Points from consensus or synthesis */}
                  {(() => {
                    const points = debateConsensus?.key_points ||
                      debateMessages.filter(m => m.phase === 'synthesis')[0]?.key_points || []
                    return points.length > 0 ? (
                      <div className="space-y-1.5 mb-3">
                        {points.map((point: string, idx: number) => (
                          <div key={idx} className="flex items-center gap-2 p-2 rounded-lg bg-bg-tertiary border border-accent/20">
                            <CheckCircle2 className="w-4 h-4 text-success shrink-0" />
                            <span className="text-sm text-text-primary">{point}</span>
                          </div>
                        ))}
                      </div>
                    ) : null
                  })()}
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  )
}
