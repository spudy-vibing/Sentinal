import { motion, AnimatePresence } from 'framer-motion'
import {
  Check,
  Loader2,
  AlertCircle,
  Zap,
  Brain,
  Users,
  FileCheck,
  ChevronDown,
  ChevronUp
} from 'lucide-react'
import { useState } from 'react'
import { useActivityStore } from '../stores/activityStore'

// Extended store type for additional fields
interface ExtendedActivityStore {
  activities: ReturnType<typeof useActivityStore>['activities']
  thinkingStream: ReturnType<typeof useActivityStore>['thinkingStream']
  activeAgents: ReturnType<typeof useActivityStore>['activeAgents']
  debatePhase: string | null
  debateMessages: unknown[]
  scenarios: unknown[]
}

type StepStatus = 'pending' | 'active' | 'complete' | 'error'

interface AnalysisStep {
  id: string
  label: string
  description: string
  status: StepStatus
  agents?: { name: string; status: string; thought?: string }[]
  timestamp?: string
}

export default function ProgressTimeline() {
  const { activities, thinkingStream, activeAgents, debatePhase, debateMessages, scenarios } = useActivityStore()
  const [expandedStep, setExpandedStep] = useState<string | null>(null)

  // Derive steps from activity state
  const steps = deriveSteps({ activities, thinkingStream, activeAgents, debatePhase, debateMessages, scenarios })

  const toggleExpand = (stepId: string) => {
    setExpandedStep(expandedStep === stepId ? null : stepId)
  }

  return (
    <div className="card h-full flex flex-col">
      <div className="p-4 border-b border-border-subtle">
        <h3 className="font-semibold text-text-primary">Analysis Progress</h3>
        <p className="text-xs text-text-muted mt-1">Real-time agent workflow</p>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-1">
          <AnimatePresence mode="popLayout">
            {steps.map((step, index) => (
              <motion.div
                key={step.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 10 }}
                transition={{ delay: index * 0.05 }}
                className="timeline-step"
              >
                {/* Vertical Line (except last) */}
                {index < steps.length - 1 && (
                  <div
                    className={`absolute left-[8px] top-[28px] bottom-[-4px] w-[2px] ${
                      step.status === 'complete' ? 'bg-success' : 'bg-border-subtle'
                    }`}
                  />
                )}

                {/* Step Dot */}
                <div className={`timeline-dot ${getStepDotClass(step.status)}`}>
                  {getStepIcon(step.status)}
                </div>

                {/* Step Content */}
                <div
                  className={`ml-7 pb-4 ${step.agents?.length ? 'cursor-pointer' : ''}`}
                  onClick={() => step.agents?.length && toggleExpand(step.id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className={`text-sm font-medium ${
                        step.status === 'active' ? 'text-accent' :
                        step.status === 'complete' ? 'text-text-primary' :
                        step.status === 'error' ? 'text-error' :
                        'text-text-muted'
                      }`}>
                        {step.label}
                      </span>
                      {step.status === 'active' && (
                        <span className="text-xs text-accent animate-pulse">In progress</span>
                      )}
                    </div>
                    {step.agents?.length ? (
                      expandedStep === step.id ?
                        <ChevronUp className="w-4 h-4 text-text-muted" /> :
                        <ChevronDown className="w-4 h-4 text-text-muted" />
                    ) : null}
                  </div>

                  <p className="text-xs text-text-muted mt-0.5">{step.description}</p>

                  {/* Agent Details (expandable) */}
                  <AnimatePresence>
                    {expandedStep === step.id && step.agents && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="mt-3 space-y-2 overflow-hidden"
                      >
                        {step.agents.map((agent) => (
                          <div
                            key={agent.name}
                            className="flex items-start gap-2 p-2 rounded-md bg-bg-tertiary"
                          >
                            <div className={`w-2 h-2 rounded-full mt-1.5 ${
                              agent.status === 'complete' ? 'bg-success' :
                              ['analyzing', 'thinking', 'active'].includes(agent.status) ? 'bg-accent animate-pulse' :
                              agent.status === 'error' ? 'bg-error' :
                              'bg-text-muted'
                            }`} />
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-medium text-text-primary">
                                  {agent.name}
                                </span>
                                <span className={`text-xs ${
                                  ['analyzing', 'active'].includes(agent.status) ? 'text-accent' :
                                  agent.status === 'complete' ? 'text-success' :
                                  'text-text-muted'
                                }`}>
                                  {agent.status}
                                </span>
                              </div>
                              {agent.thought && (
                                <p className="text-xs text-text-secondary mt-1 truncate">
                                  {agent.thought}
                                </p>
                              )}
                            </div>
                          </div>
                        ))}
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Timestamp */}
                  {step.timestamp && (
                    <span className="text-xs text-text-muted mt-1 block">
                      {step.timestamp}
                    </span>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {/* Empty State */}
        {steps.length === 1 && steps[0].status === 'pending' && (
          <div className="text-center py-8 mt-4">
            <Zap className="w-8 h-8 text-text-muted mx-auto mb-2" />
            <p className="text-sm text-text-secondary">Ready for analysis</p>
            <p className="text-xs text-text-muted mt-1">Inject an event to begin</p>
          </div>
        )}
      </div>
    </div>
  )
}

function getStepDotClass(status: StepStatus): string {
  switch (status) {
    case 'complete':
      return 'timeline-dot-complete'
    case 'active':
      return 'timeline-dot-active'
    case 'error':
      return 'bg-error border-error text-white'
    default:
      return 'timeline-dot-pending'
  }
}

function getStepIcon(status: StepStatus) {
  switch (status) {
    case 'complete':
      return <Check className="w-3 h-3" />
    case 'active':
      return <Loader2 className="w-3 h-3 animate-spin" />
    case 'error':
      return <AlertCircle className="w-3 h-3" />
    default:
      return null
  }
}

function deriveSteps(store: ExtendedActivityStore): AnalysisStep[] {
  const { activities, thinkingStream, activeAgents, debatePhase, debateMessages, scenarios } = store
  const hasActivities = activities.length > 0
  const hasThinking = Object.keys(thinkingStream).length > 0
  const hasActiveAgents = activeAgents.length > 0

  // Check activity types
  const gatewayActivity = activities.find(a => a.agent_type === 'gateway')
  const analysisActivities = activities.filter(a =>
    ['drift', 'tax', 'compliance'].includes(a.agent_type)
  )
  const completedAnalysis = analysisActivities.filter(a => a.status === 'complete')

  // Check coordinator completion for final status
  const coordinatorComplete = activities.some(a =>
    a.agent_type === 'coordinator' && a.status === 'complete'
  )

  // Build agent list for analysis step
  const analysisAgents = ['Drift Agent', 'Tax Agent', 'Compliance Agent'].map(name => {
    const agentType = name.split(' ')[0].toLowerCase()
    // Get all activities for this agent, find the most recent/best status
    const agentActivities = analysisActivities.filter(a =>
      a.agent_name === name || a.agent_type === agentType
    )
    // Check if any activity is "complete" - this takes priority
    const hasComplete = agentActivities.some(a => a.status === 'complete')
    const latestActivity = agentActivities[agentActivities.length - 1]
    const thinking = thinkingStream[name]
    const isActive = activeAgents.some(a => a.name === name)

    return {
      name,
      status: hasComplete ? 'complete' :
              isActive || thinking ? 'analyzing' :
              latestActivity ? latestActivity.status : 'pending',
      thought: thinking?.thoughts?.[thinking.thoughts.length - 1]
    }
  })

  const steps: AnalysisStep[] = [
    {
      id: 'receive',
      label: 'Event Received',
      description: gatewayActivity ? 'Market event captured' : 'Waiting for event injection',
      status: gatewayActivity ? 'complete' : hasActivities ? 'complete' : 'pending',
      timestamp: gatewayActivity?.timestamp ? formatTime(gatewayActivity.timestamp) : undefined
    },
    {
      id: 'analyze',
      label: 'Agent Analysis',
      description: 'Specialized agents processing event',
      status: completedAnalysis.length === 3 ? 'complete' :
              (hasThinking || hasActiveAgents || analysisActivities.length > 0) ? 'active' :
              gatewayActivity ? 'pending' : 'pending',
      agents: analysisAgents
    },
    {
      id: 'debate',
      label: 'Consensus Building',
      description: 'Agents debating recommendations',
      status: debatePhase === 'consensus' ? 'complete' :
              debatePhase || (debateMessages && debateMessages.length > 0) ? 'active' :
              completedAnalysis.length === 3 ? 'pending' : 'pending'
    },
    {
      id: 'recommend',
      label: 'Recommendations',
      description: 'Final action plan generated',
      status: coordinatorComplete || (scenarios && scenarios.length > 0) ? 'complete' : 'pending'
    }
  ]

  return steps
}

function formatTime(timestamp: string): string {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  if (isNaN(date.getTime())) return ''
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  })
}
