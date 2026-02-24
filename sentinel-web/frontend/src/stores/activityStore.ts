import { create } from 'zustand'

interface Agent {
  name: string
  type: string
  status: 'idle' | 'analyzing' | 'thinking' | 'debating' | 'complete' | 'error'
}

interface AgentActivity {
  id?: string  // For deduplication
  agent_name: string
  agent_type: string
  status: string
  message: string
  timestamp: string
  data?: Record<string, unknown>
  progress?: number
}

interface ThinkingState {
  text: string
  lastUpdate: number
  thoughts: string[]  // Individual thought items instead of accumulating string
}

interface DebateMessage {
  agent_id?: string
  agent_name: string
  phase?: string
  position: string
  message?: string  // Backend sends 'message'
  argument?: string // Also support 'argument' for flexibility
  confidence: number
  key_points?: string[]
  timestamp?: string
}

interface MerkleBlock {
  block_hash: string
  event_type: string
  timestamp: string
}

interface Scenario {
  id: string
  title: string
  description: string
  score: number
  is_recommended: boolean
  actions: Array<{
    type: string
    ticker: string
    quantity: number
  }>
}

interface CompletedAgentSummary {
  name: string
  type: string
  summary: string
  thoughts: string[]
  completedAt: number
}

interface ActivityState {
  // Connection
  isConnected: boolean
  setConnected: (connected: boolean) => void

  // Agents
  activeAgents: Agent[]
  setActiveAgents: (agents: Agent[]) => void
  addActiveAgent: (agent: Agent) => void
  removeActiveAgent: (name: string) => void

  // Activity Feed (with deduplication)
  activities: AgentActivity[]
  addActivity: (activity: AgentActivity) => void
  clearActivities: () => void

  // Thinking Stream (improved - stores individual thoughts, not accumulated string)
  thinkingStream: Record<string, ThinkingState>
  addThought: (agentName: string, thought: string) => void
  clearThinking: (agentName: string) => void
  clearAllThinking: () => void

  // Completed Agents (persists after completion for display)
  completedAgents: CompletedAgentSummary[]
  addCompletedAgent: (agent: CompletedAgentSummary) => void
  clearCompletedAgents: () => void

  // Debate
  debateMessages: DebateMessage[]
  addDebateMessage: (message: DebateMessage) => void
  clearDebate: () => void

  // Merkle Chain
  merkleBlocks: MerkleBlock[]
  addMerkleBlock: (block: MerkleBlock) => void

  // Scenarios
  scenarios: Scenario[]
  setScenarios: (scenarios: Scenario[]) => void
  clearScenarios: () => void

  // Debate Phase
  debatePhase: string | null
  debateQuestion: string | null
  setDebatePhase: (phase: string | null, question?: string | null) => void

  // Chat
  chatOpen: boolean
  setChatOpen: (open: boolean) => void

  // Analysis state
  currentEventId: string | null
  setCurrentEventId: (id: string | null) => void

  // Portfolio state
  selectedPortfolioId: string | null
  setSelectedPortfolioId: (id: string | null) => void

  // Portfolio selector UI state
  portfolioSelectorOpen: boolean
  setPortfolioSelectorOpen: (open: boolean) => void
  togglePortfolioSelector: () => void
}

// Helper to generate activity ID for deduplication
function getActivityId(activity: AgentActivity): string {
  return `${activity.agent_type}-${activity.status}-${activity.message.slice(0, 50)}`
}

export const useActivityStore = create<ActivityState>((set, get) => ({
  // Connection
  isConnected: false,
  setConnected: (connected) => set({ isConnected: connected }),

  // Agents
  activeAgents: [],
  setActiveAgents: (agents) => set({ activeAgents: agents }),
  addActiveAgent: (agent) =>
    set((state) => ({
      activeAgents: state.activeAgents.some((a) => a.name === agent.name)
        ? state.activeAgents.map((a) => (a.name === agent.name ? agent : a))
        : [...state.activeAgents, agent],
    })),
  removeActiveAgent: (name) =>
    set((state) => ({
      activeAgents: state.activeAgents.filter((a) => a.name !== name),
    })),

  // Activity Feed with deduplication
  activities: [],
  addActivity: (activity) =>
    set((state) => {
      const activityId = getActivityId(activity)
      const activityWithId = { ...activity, id: activityId }

      // Check if this activity already exists (deduplication)
      const exists = state.activities.some(a => a.id === activityId)
      if (exists) {
        return state // Don't add duplicate
      }

      // When agent completes, save to completedAgents with thinking history
      if (activity.status === 'complete' && activity.agent_type) {
        const agentName = activity.agent_name
        const thinkingState = state.thinkingStream[agentName]
        const newThinkingStream = { ...state.thinkingStream }
        delete newThinkingStream[agentName]

        // Save completed agent with summary
        const completedAgent: CompletedAgentSummary = {
          name: agentName,
          type: activity.agent_type,
          summary: activity.message,
          thoughts: thinkingState?.thoughts || [],
          completedAt: Date.now()
        }

        return {
          activities: [...state.activities.slice(-49), activityWithId], // Keep last 50
          thinkingStream: newThinkingStream,
          completedAgents: [
            ...state.completedAgents.filter(a => a.name !== agentName),
            completedAgent
          ]
        }
      }

      return {
        activities: [...state.activities.slice(-49), activityWithId], // Keep last 50
      }
    }),
  clearActivities: () => set({
    activities: [],
    thinkingStream: {},
    completedAgents: [],
    debateMessages: [],
    debatePhase: null,
    debateQuestion: null,
    scenarios: []
  }),

  // Thinking Stream - stores individual thoughts, max 6 per agent
  thinkingStream: {},
  addThought: (agentName, thought) =>
    set((state) => {
      const current = state.thinkingStream[agentName] || { text: '', lastUpdate: 0, thoughts: [] }
      const now = Date.now()

      // Prevent duplicate thoughts (within 500ms window)
      if (now - current.lastUpdate < 500 && current.thoughts.includes(thought)) {
        return state
      }

      // Keep only last 5 thoughts to prevent overflow
      const newThoughts = [...current.thoughts, thought].slice(-5)

      return {
        thinkingStream: {
          ...state.thinkingStream,
          [agentName]: {
            text: thought, // Current thought (latest)
            lastUpdate: now,
            thoughts: newThoughts
          }
        }
      }
    }),
  clearThinking: (agentName) =>
    set((state) => {
      const newStream = { ...state.thinkingStream }
      delete newStream[agentName]
      return { thinkingStream: newStream }
    }),
  clearAllThinking: () => set({ thinkingStream: {} }),

  // Completed Agents - persist after completion
  completedAgents: [],
  addCompletedAgent: (agent) =>
    set((state) => {
      // Avoid duplicates
      if (state.completedAgents.some(a => a.name === agent.name)) {
        return {
          completedAgents: state.completedAgents.map(a =>
            a.name === agent.name ? agent : a
          )
        }
      }
      return {
        completedAgents: [...state.completedAgents, agent]
      }
    }),
  clearCompletedAgents: () => set({ completedAgents: [] }),

  // Debate
  debateMessages: [],
  addDebateMessage: (message) =>
    set((state) => ({
      debateMessages: [...state.debateMessages, message],
    })),
  clearDebate: () => set({ debateMessages: [] }),

  // Merkle Chain
  merkleBlocks: [],
  addMerkleBlock: (block) =>
    set((state) => ({
      merkleBlocks: [...state.merkleBlocks.slice(-49), block], // Keep last 50
    })),

  // Scenarios
  scenarios: [],
  setScenarios: (scenarios) => set({ scenarios }),
  clearScenarios: () => set({ scenarios: [] }),

  // Debate Phase
  debatePhase: null,
  debateQuestion: null,
  setDebatePhase: (phase, question = null) => set({ debatePhase: phase, debateQuestion: question }),

  // Chat
  chatOpen: false,
  setChatOpen: (open) => set({ chatOpen: open }),

  // Analysis state
  currentEventId: null,
  setCurrentEventId: (id) => set({ currentEventId: id }),

  // Portfolio state
  selectedPortfolioId: null,
  setSelectedPortfolioId: (id) => set({ selectedPortfolioId: id }),

  // Portfolio selector UI state
  portfolioSelectorOpen: false,
  setPortfolioSelectorOpen: (open) => set({ portfolioSelectorOpen: open }),
  togglePortfolioSelector: () => set((state) => ({ portfolioSelectorOpen: !state.portfolioSelectorOpen })),
}))
