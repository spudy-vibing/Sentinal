import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Users,
  Brain,
  MessageSquare,
  Zap,
  ChevronRight,
  ThumbsUp,
  ThumbsDown,
  Scale,
} from 'lucide-react'
import { useActivityStore } from '../stores/activityStore'

const agents = [
  { id: 'drift', name: 'Drift Agent', color: 'text-info', bgColor: 'bg-info/10' },
  { id: 'tax', name: 'Tax Agent', color: 'text-success', bgColor: 'bg-success/10' },
  { id: 'compliance', name: 'Compliance Agent', color: 'text-warning', bgColor: 'bg-warning/10' },
  { id: 'scenario', name: 'Scenario Agent', color: 'text-accent', bgColor: 'bg-accent/10' },
]

export default function WarRoom() {
  const [debateTopic, setDebateTopic] = useState<string | null>(null)
  const [isDebating, setIsDebating] = useState(false)
  const { debateMessages, clearDebate, addDebateMessage, setDebatePhase } = useActivityStore()

  const startDebate = (topic: string) => {
    setDebateTopic(topic)
    setIsDebating(true)
    clearDebate()
    // In production, this would trigger a real debate via WebSocket
  }

  const simulateDebate = () => {
    // Demo debate messages for demonstration
    const demoMessages = [
      {
        agent_name: 'Drift Agent',
        agent_id: 'drift',
        position: 'for',
        message: 'NVDA position is 18% above target allocation. Immediate rebalancing is critical to maintain risk parameters.',
        confidence: 92,
        key_points: ['concentration risk', 'volatility exposure']
      },
      {
        agent_name: 'Tax Agent',
        agent_id: 'tax',
        position: 'against',
        message: 'Selling now triggers $45,000 in short-term capital gains. Waiting 3 weeks converts to long-term treatment, saving $12,000.',
        confidence: 88,
        key_points: ['tax efficiency', 'holding period']
      },
      {
        agent_name: 'Compliance Agent',
        agent_id: 'compliance',
        position: 'neutral',
        message: 'Both approaches are compliant. Recommend documenting rationale for either decision in audit trail.',
        confidence: 95,
        key_points: ['regulatory compliance', 'documentation']
      },
      {
        agent_name: 'Coordinator',
        agent_id: 'coordinator',
        position: 'synthesis',
        message: 'Compromise: Partial rebalance now (reduce to 15%), full rebalance after holding period. Balances risk reduction with tax efficiency.',
        confidence: 90,
        key_points: ['balanced approach', 'phased execution']
      }
    ]

    // Clear previous messages and set phase
    clearDebate()
    setDebatePhase('opening', debateTopic?.replace('_', ' ') || 'Agent Debate')

    // Add messages with staggered timing for visual effect
    demoMessages.forEach((msg, index) => {
      setTimeout(() => {
        addDebateMessage(msg)
        // Set consensus phase after last message
        if (index === demoMessages.length - 1) {
          setTimeout(() => setDebatePhase('consensus'), 500)
        }
      }, index * 800)
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary flex items-center gap-3">
            <Users className="w-6 h-6 text-accent" />
            Multi-Agent War Room
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Watch agents collaborate, debate, and reach consensus
          </p>
        </div>
      </div>

      {/* Agent Status Grid */}
      <div className="grid grid-cols-4 gap-4">
        {agents.map((agent, index) => (
          <motion.div
            key={agent.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className={`card p-4 border-l-2 ${agent.color.replace('text-', 'border-')}`}
          >
            <div className="flex items-center justify-between mb-3">
              <span className={`font-medium ${agent.color}`}>{agent.name}</span>
              <span className="status-dot status-dot-idle" />
            </div>
            <div className="text-xs text-text-muted">
              Ready for analysis
            </div>
          </motion.div>
        ))}
      </div>

      {/* Debate Topics */}
      <div className="card p-6">
        <h2 className="text-lg font-medium text-text-primary mb-4 flex items-center gap-2">
          <Scale className="w-5 h-5 text-accent" />
          Start Agent Debate
        </h2>
        <p className="text-sm text-text-secondary mb-4">
          Select a topic to have agents debate and reach consensus
        </p>

        <div className="grid grid-cols-2 gap-4">
          <DebateTopicCard
            title="Sell NVDA Now vs. Wait"
            description="Should we accept the wash sale penalty to reduce concentration immediately?"
            onClick={() => startDebate('nvda_timing')}
            isActive={debateTopic === 'nvda_timing'}
          />
          <DebateTopicCard
            title="AMD Substitute Risk"
            description="Is AMD a safe substitute or does it introduce new correlation risks?"
            onClick={() => startDebate('amd_risk')}
            isActive={debateTopic === 'amd_risk'}
          />
          <DebateTopicCard
            title="Tax Harvesting Priority"
            description="Which losses should be harvested first given upcoming deadlines?"
            onClick={() => startDebate('tax_priority')}
            isActive={debateTopic === 'tax_priority'}
          />
          <DebateTopicCard
            title="Rebalance Aggressiveness"
            description="How aggressively should we rebalance given current market conditions?"
            onClick={() => startDebate('rebalance_level')}
            isActive={debateTopic === 'rebalance_level'}
          />
        </div>
      </div>

      {/* Debate Arena */}
      <AnimatePresence>
        {debateTopic && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="card p-6"
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-medium text-text-primary flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-accent" />
                Debate: {debateTopic.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}
              </h2>
              <button
                onClick={() => setDebateTopic(null)}
                className="btn-ghost text-sm"
              >
                Close
              </button>
            </div>

            {/* Debate Messages */}
            <div className="space-y-4 mb-6 max-h-96 overflow-y-auto">
              {debateMessages.length === 0 ? (
                <div className="text-center py-8">
                  <Brain className="w-12 h-12 text-text-muted mx-auto mb-3 animate-pulse" />
                  <p className="text-text-muted">Agents are formulating their positions...</p>
                </div>
              ) : (
                debateMessages.map((msg, idx) => (
                  <DebateMessageCard key={idx} message={msg} />
                ))
              )}
            </div>

            {/* Demo: Simulate Debate */}
            <div className="flex justify-center">
              <button
                onClick={() => simulateDebate()}
                className="btn-primary"
              >
                <Zap className="w-4 h-4" />
                Simulate Debate (Demo)
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

interface DebateTopicCardProps {
  title: string
  description: string
  onClick: () => void
  isActive: boolean
}

function DebateTopicCard({ title, description, onClick, isActive }: DebateTopicCardProps) {
  return (
    <button
      onClick={onClick}
      className={`text-left p-4 rounded-lg border transition-all ${
        isActive
          ? 'bg-accent/10 border-accent/30 shadow-glow'
          : 'bg-bg-tertiary border-border-subtle hover:border-border-default'
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="font-medium text-text-primary">{title}</span>
        <ChevronRight className="w-4 h-4 text-text-muted" />
      </div>
      <p className="text-sm text-text-secondary">{description}</p>
    </button>
  )
}

interface DebateMessageProps {
  message: {
    agent_name: string
    position: string
    message?: string
    argument?: string
    confidence: number
    key_points?: string[]
  }
}

function DebateMessageCard({ message }: DebateMessageProps) {
  const getAgentColor = (name: string) => {
    if (name.toLowerCase().includes('drift')) return 'border-info'
    if (name.toLowerCase().includes('tax')) return 'border-success'
    if (name.toLowerCase().includes('compliance')) return 'border-warning'
    return 'border-accent'
  }

  const getPositionIcon = (position: string) => {
    if (position === 'for') return <ThumbsUp className="w-4 h-4 text-success" />
    if (position === 'against') return <ThumbsDown className="w-4 h-4 text-error" />
    return <Scale className="w-4 h-4 text-warning" />
  }

  // Confidence is already 0-100 from our demo
  const confidenceDisplay = message.confidence > 1 ? message.confidence : message.confidence * 100

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className={`p-4 rounded-lg bg-bg-tertiary border-l-2 ${getAgentColor(message.agent_name)}`}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="font-medium text-text-primary">{message.agent_name}</span>
        <div className="flex items-center gap-2">
          {getPositionIcon(message.position)}
          <span className="text-xs text-text-muted">
            {confidenceDisplay.toFixed(0)}% confident
          </span>
        </div>
      </div>
      <p className="text-sm text-text-secondary">{message.message || message.argument}</p>
      {message.key_points && message.key_points.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {message.key_points.map((point, idx) => (
            <span key={idx} className="text-xs px-2 py-0.5 bg-bg-secondary text-text-muted rounded">
              {point}
            </span>
          ))}
        </div>
      )}
    </motion.div>
  )
}

