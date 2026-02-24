/**
 * SENTINEL V2 — TypeScript Types
 */

// Agent Types
export type AgentType = 'drift' | 'tax' | 'compliance' | 'scenario' | 'coordinator'
export type AgentStatus = 'idle' | 'analyzing' | 'thinking' | 'debating' | 'complete' | 'error'

export interface Agent {
  name: string
  type: AgentType
  status: AgentStatus
}

export interface AgentActivity {
  agent_name: string
  agent_type: AgentType
  status: AgentStatus
  message: string
  timestamp: string
  data?: Record<string, unknown>
  progress?: number
}

// Portfolio Types
export interface Holding {
  ticker: string
  quantity: number
  current_price: number
  market_value: number
  portfolio_weight: number
  cost_basis: number
  unrealized_gain_loss: number
  sector: string
  asset_class: string
}

export interface Portfolio {
  portfolio_id: string
  client_id: string
  name: string
  aum_usd: number
  cash_available: number
  holdings: Holding[]
  last_rebalance: string
  risk_tolerance: string
  tax_sensitivity: number
  concentration_limit: number
}

export interface PortfolioSummary {
  portfolio_id: string
  name: string
  aum_usd: number
  holdings_count: number
  top_holding: string
  top_holding_weight: number
}

// Scenario Types
export interface ActionStep {
  type: 'buy' | 'sell' | 'hold'
  ticker: string
  quantity: number
  rationale?: string
}

export interface ScenarioMetrics {
  risk_reduction: number
  tax_savings: number
  goal_alignment: number
  transaction_cost: number
  urgency: number
}

export interface Scenario {
  id: string
  title: string
  description: string
  score: number
  is_recommended: boolean
  actions: ActionStep[]
  metrics: ScenarioMetrics
  risks: string[]
  expected_outcomes: Record<string, number>
}

// Chat Types
export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatRequest {
  message: string
  history: ChatMessage[]
  portfolio_id?: string
  include_context?: boolean
}

export interface ChatResponse {
  response: string
  context_used: string[]
}

// Event Types
export interface MarketEvent {
  event_type: string
  data: Record<string, unknown>
  portfolio_id: string
  run_debate?: boolean
  stream_thinking?: boolean
}

export interface EventPreset {
  id: string
  name: string
  description: string
  data: Record<string, unknown>
}

// Debate Types
export interface DebateMessage {
  agent_name: string
  position: 'pro' | 'con' | 'neutral'
  argument: string
  confidence: number
  references: string[]
  timestamp: string
}

export interface DebateResult {
  winner?: string
  consensus: string
  key_points: string[]
  final_recommendation: string
  vote_breakdown: Record<string, number>
}

// Merkle Chain Types
export interface MerkleBlock {
  block_hash: string
  previous_hash?: string
  event_type: string
  event_data?: Record<string, unknown>
  timestamp: string
  signature?: string
}

// WebSocket Message Types
export interface WebSocketMessage {
  type: string
  data: Record<string, unknown>
  timestamp: string
}

// API Response Types
export interface ApiError {
  detail: string
}

export interface ApprovalResponse {
  status: string
  scenario_id: string
  merkle_hash: string
  timestamp: string
  message: string
}
