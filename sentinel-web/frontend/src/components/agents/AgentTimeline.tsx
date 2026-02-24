import { motion, AnimatePresence } from 'framer-motion'
import { useActivityStore } from '../../stores/activityStore'
import AgentNode from './AgentNode'
import { Activity, Zap } from 'lucide-react'

const AGENTS = [
  {
    id: 'coordinator',
    name: 'Coordinator',
    description: 'Orchestration & dispatch',
    type: 'coordinator' as const,
  },
  {
    id: 'drift',
    name: 'Drift Agent',
    description: 'Portfolio drift & concentration',
    type: 'drift' as const,
  },
  {
    id: 'tax',
    name: 'Tax Agent',
    description: 'Tax optimization & wash sales',
    type: 'tax' as const,
  },
  {
    id: 'compliance',
    name: 'Compliance Agent',
    description: 'Regulatory constraints',
    type: 'compliance' as const,
  },
  {
    id: 'scenario',
    name: 'Scenario Agent',
    description: 'Strategy generation',
    type: 'scenario' as const,
  },
]

export default function AgentTimeline() {
  const { activities, activeAgents, thinkingStream } = useActivityStore()

  const getAgentState = (agentId: string) => {
    const agent = activeAgents.find(
      (a) => a.name.toLowerCase().includes(agentId) || a.type === agentId
    )
    if (agent) return agent.status
    return 'idle'
  }

  const getAgentMessage = (agentId: string) => {
    const agentActivities = activities.filter(
      (a) =>
        a.agent_name.toLowerCase().includes(agentId) ||
        a.agent_type === agentId
    )
    if (agentActivities.length === 0) return null
    return agentActivities[agentActivities.length - 1].message
  }

  const getAgentThinking = (agentId: string) => {
    const key = Object.keys(thinkingStream).find((k) =>
      k.toLowerCase().includes(agentId)
    )
    return key ? thinkingStream[key] : null
  }

  const isProcessing = activeAgents.length > 0

  return (
    <div className="card p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-medium text-text-primary flex items-center gap-2">
            <Activity className="w-5 h-5 text-accent" />
            Agent Pipeline
          </h2>
          <p className="text-sm text-text-muted">Real-time execution status</p>
        </div>

        <AnimatePresence>
          {isProcessing && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="flex items-center gap-2 px-3 py-1.5 bg-accent/10 border border-accent/30 rounded-full"
            >
              <Zap className="w-3 h-3 text-accent animate-pulse" />
              <span className="text-xs font-medium text-accent">Processing</span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Timeline */}
      <div className="relative">
        {/* Connection line */}
        <div className="absolute left-6 top-8 bottom-8 w-px bg-gradient-to-b from-border-subtle via-accent/30 to-border-subtle" />

        {/* Animated flow indicator */}
        <AnimatePresence>
          {isProcessing && (
            <motion.div
              initial={{ top: '2rem', opacity: 0 }}
              animate={{
                top: ['2rem', '90%'],
                opacity: [0, 1, 1, 0],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'linear',
              }}
              className="absolute left-[22px] w-2 h-8 bg-gradient-to-b from-transparent via-accent to-transparent rounded-full"
              style={{ filter: 'blur(2px)' }}
            />
          )}
        </AnimatePresence>

        {/* Agent nodes */}
        <div className="space-y-3">
          {AGENTS.map((agent, index) => (
            <AgentNode
              key={agent.id}
              id={agent.id}
              name={agent.name}
              description={agent.description}
              type={agent.type}
              state={getAgentState(agent.id)}
              message={getAgentMessage(agent.id)}
              thinking={getAgentThinking(agent.id)}
              delay={index * 0.1}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
