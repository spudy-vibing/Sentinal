import { useState, useEffect, useCallback, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  GitBranch,
  Check,
  ChevronRight,
  ArrowRight,
  TrendingUp,
  Shield,
  Clock,
  DollarSign,
  AlertTriangle,
  Sparkles,
  RefreshCw,
  Loader2,
  XCircle,
  Inbox,
} from 'lucide-react'
import { useActivityStore } from '../stores/activityStore'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const STORAGE_KEY = 'sentinel_approved_scenarios'

interface Scenario {
  id: string
  title: string
  description: string
  score: number
  is_recommended: boolean
  status?: 'proposed' | 'approved' | 'rejected'
  actions: Array<{
    type: string
    ticker: string
    quantity: number
    rationale: string
  }>
  metrics: {
    risk_reduction: number
    tax_savings: number
    goal_alignment: number
    transaction_cost: number
    urgency: number
  }
  risks: string[]
  expected_outcomes: Record<string, number>
}

interface ApprovalInfo {
  merkleHash: string
  approvedAt: string
}

// Load approved scenarios from localStorage
function loadApprovedScenarios(): Record<string, ApprovalInfo> {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored ? JSON.parse(stored) : {}
  } catch {
    return {}
  }
}

// Save approved scenarios to localStorage
function saveApprovedScenarios(data: Record<string, ApprovalInfo>) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  } catch (err) {
    console.error('Failed to save approval state:', err)
  }
}

export default function Scenarios() {
  const [apiScenarios, setApiScenarios] = useState<Scenario[]>([])
  const [selectedScenarioId, setSelectedScenarioId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [isApproving, setIsApproving] = useState(false)
  const [approvalError, setApprovalError] = useState<string | null>(null)
  const [showConfirmDialog, setShowConfirmDialog] = useState(false)
  const [approvedScenarios, setApprovedScenarios] = useState<Record<string, ApprovalInfo>>(loadApprovedScenarios)
  const { scenarios: storeScenarios } = useActivityStore()

  // Use real-time scenarios from store if available, otherwise API scenarios
  const scenarios = useMemo(() => {
    return storeScenarios.length > 0 ? storeScenarios as Scenario[] : apiScenarios
  }, [storeScenarios, apiScenarios])

  // Get selected scenario from current scenarios array (prevents stale data)
  const selectedScenario = useMemo(() => {
    if (!selectedScenarioId) return null
    return scenarios.find(s => s.id === selectedScenarioId) || null
  }, [scenarios, selectedScenarioId])

  // Persist approved scenarios to localStorage whenever it changes
  useEffect(() => {
    saveApprovedScenarios(approvedScenarios)
  }, [approvedScenarios])

  // Fetch scenarios on mount
  useEffect(() => {
    fetchScenarios()
  }, [])

  // Auto-select recommended scenario when scenarios change
  useEffect(() => {
    if (scenarios.length > 0 && !selectedScenarioId) {
      const recommended = scenarios.find((s) => s.is_recommended)
      setSelectedScenarioId(recommended?.id || scenarios[0]?.id || null)
    }
  }, [scenarios, selectedScenarioId])

  // Clear approval error when scenario changes
  useEffect(() => {
    setApprovalError(null)
  }, [selectedScenarioId])

  const fetchScenarios = useCallback(async () => {
    setLoadError(null)
    try {
      const response = await fetch(`${API_URL}/api/scenarios`)
      if (response.ok) {
        const data = await response.json()
        setApiScenarios(data)
      } else {
        setLoadError('Failed to load scenarios')
      }
    } catch (err) {
      console.error('Failed to fetch scenarios:', err)
      setLoadError('Network error. Please check your connection.')
    } finally {
      setIsLoading(false)
    }
  }, [])

  const handleRefresh = useCallback(() => {
    setIsLoading(true)
    setSelectedScenarioId(null) // Clear selection to prevent stale data
    fetchScenarios()
  }, [fetchScenarios])

  const handleApprove = useCallback(async () => {
    if (!selectedScenario || isApproving) return

    setShowConfirmDialog(false)
    setIsApproving(true)
    setApprovalError(null)

    try {
      const response = await fetch(`${API_URL}/api/scenarios/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario_id: selectedScenario.id,
          approver_id: 'advisor_001',
          notes: 'Approved via Sentinel V2 UI',
        }),
      })

      if (response.ok) {
        const data = await response.json()
        // Store approval info persistently
        setApprovedScenarios(prev => ({
          ...prev,
          [selectedScenario.id]: {
            merkleHash: data.merkle_hash,
            approvedAt: new Date().toISOString()
          }
        }))
      } else {
        const errorData = await response.json().catch(() => ({}))
        setApprovalError(errorData.detail || 'Failed to approve scenario')
      }
    } catch (err) {
      console.error('Failed to approve scenario:', err)
      setApprovalError('Network error. Please try again.')
    } finally {
      setIsApproving(false)
    }
  }, [selectedScenario, isApproving])

  // Check if current scenario is approved
  const isCurrentScenarioApproved = selectedScenario ?
    !!(approvedScenarios[selectedScenario.id] || selectedScenario.status === 'approved') : false
  const currentApprovalInfo = selectedScenario ? approvedScenarios[selectedScenario.id] : null

  return (
    <div className="space-y-6">
      {/* Confirmation Dialog */}
      <AnimatePresence>
        {showConfirmDialog && selectedScenario && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={() => setShowConfirmDialog(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-bg-secondary rounded-xl p-6 max-w-md w-full mx-4 shadow-xl border border-border-subtle"
            >
              <h3 className="text-lg font-semibold text-text-primary mb-2">
                Confirm Scenario Approval
              </h3>
              <p className="text-sm text-text-secondary mb-4">
                You are about to approve <strong>"{selectedScenario.title}"</strong>.
                This action will be logged to the Merkle chain and cannot be undone.
              </p>
              <div className="bg-bg-tertiary rounded-lg p-3 mb-4">
                <p className="text-xs text-text-muted mb-1">Actions to be executed:</p>
                {selectedScenario.actions.map((action, idx) => (
                  <p key={idx} className="text-sm text-text-primary">
                    • {action.type.toUpperCase()} {action.quantity.toLocaleString()} {action.ticker}
                  </p>
                ))}
              </div>
              <div className="flex gap-3 justify-end">
                <button
                  onClick={() => setShowConfirmDialog(false)}
                  className="btn-ghost"
                >
                  Cancel
                </button>
                <button
                  onClick={handleApprove}
                  className="btn-primary"
                >
                  Confirm Approval
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary flex items-center gap-3">
            <GitBranch className="w-6 h-6 text-accent" />
            Scenario Analysis
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            AI-generated rebalancing strategies ranked by utility score
          </p>
        </div>
        <div className="flex items-center gap-3">
          {storeScenarios.length > 0 && (
            <span className="px-3 py-1 text-xs font-medium bg-success/10 text-success rounded-full flex items-center gap-1">
              <span className="w-1.5 h-1.5 bg-success rounded-full animate-pulse" />
              Live Analysis
            </span>
          )}
          <button
            onClick={handleRefresh}
            disabled={isLoading}
            className="btn-ghost p-2"
            title="Refresh scenarios"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Loading State */}
      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-6 h-6 text-accent animate-spin" />
          <span className="ml-3 text-text-muted">Loading scenarios...</span>
        </div>
      ) : loadError ? (
        /* Error State */
        <div className="flex flex-col items-center justify-center py-20">
          <XCircle className="w-12 h-12 text-error mb-4" />
          <p className="text-text-primary font-medium mb-2">Failed to Load Scenarios</p>
          <p className="text-sm text-text-muted mb-4">{loadError}</p>
          <button onClick={handleRefresh} className="btn-primary">
            <RefreshCw className="w-4 h-4" />
            Try Again
          </button>
        </div>
      ) : scenarios.length === 0 ? (
        /* Empty State */
        <div className="flex flex-col items-center justify-center py-20">
          <Inbox className="w-12 h-12 text-text-muted mb-4" />
          <p className="text-text-primary font-medium mb-2">No Scenarios Available</p>
          <p className="text-sm text-text-muted mb-4">
            Run an analysis from the Dashboard to generate rebalancing scenarios.
          </p>
          <button onClick={handleRefresh} className="btn-ghost">
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-3 gap-6">
          {/* Scenario List */}
          <div className="col-span-1 space-y-3">
            {scenarios.map((scenario, index) => (
              <motion.button
                key={scenario.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                onClick={() => setSelectedScenarioId(scenario.id)}
                className={`w-full text-left p-4 rounded-lg border transition-all ${
                  selectedScenario?.id === scenario.id
                    ? 'bg-accent/10 border-accent/30 shadow-glow'
                    : 'bg-bg-elevated border-border-subtle hover:border-border-default'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-text-primary">
                    {scenario.title}
                  </span>
                  <div className="flex items-center gap-1.5">
                    {approvedScenarios[scenario.id] && (
                      <span className="badge badge-success">
                        <Check className="w-3 h-3" />
                        Approved
                      </span>
                    )}
                    {scenario.is_recommended && !approvedScenarios[scenario.id] && (
                      <span className="badge badge-accent">
                        <Sparkles className="w-3 h-3" />
                        Top
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-2xl font-bold text-accent">
                    {scenario.score.toFixed(1)}
                  </span>
                  <ChevronRight className="w-4 h-4 text-text-muted" />
                </div>
              </motion.button>
            ))}
          </div>

          {/* Scenario Detail */}
          <div className="col-span-2">
            <AnimatePresence mode="wait">
              {selectedScenario && (
                <motion.div
                  key={selectedScenario.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="card p-6 space-y-6"
                >
                  {/* Header */}
                  <div>
                    <div className="flex items-center gap-3 mb-2">
                      <h2 className="text-xl font-bold text-text-primary">
                        {selectedScenario.title}
                      </h2>
                      {isCurrentScenarioApproved && (
                        <span className="badge badge-success">
                          <Check className="w-3 h-3" />
                          Approved
                        </span>
                      )}
                      {selectedScenario.is_recommended && !isCurrentScenarioApproved && (
                        <span className="badge badge-accent">Recommended</span>
                      )}
                    </div>
                    <p className="text-text-secondary">
                      {selectedScenario.description}
                    </p>
                  </div>

                  {/* Metrics */}
                  <div className="grid grid-cols-5 gap-4">
                    <MetricPill
                      icon={Shield}
                      label="Risk"
                      value={selectedScenario.metrics.risk_reduction}
                    />
                    <MetricPill
                      icon={DollarSign}
                      label="Tax"
                      value={selectedScenario.metrics.tax_savings}
                    />
                    <MetricPill
                      icon={TrendingUp}
                      label="Goals"
                      value={selectedScenario.metrics.goal_alignment}
                    />
                    <MetricPill
                      icon={Clock}
                      label="Cost"
                      value={10 - selectedScenario.metrics.transaction_cost}
                    />
                    <MetricPill
                      icon={AlertTriangle}
                      label="Urgency"
                      value={selectedScenario.metrics.urgency}
                    />
                  </div>

                  {/* Actions */}
                  <div>
                    <h3 className="text-sm font-medium text-text-muted uppercase tracking-wider mb-3">
                      Proposed Actions
                    </h3>
                    <div className="space-y-2">
                      {selectedScenario.actions.map((action, idx) => (
                        <div
                          key={idx}
                          className="flex items-center gap-3 p-3 bg-bg-tertiary rounded-md"
                        >
                          <span
                            className={`badge ${
                              action.type === 'buy'
                                ? 'badge-success'
                                : action.type === 'sell'
                                ? 'badge-error'
                                : 'badge-info'
                            }`}
                          >
                            {action.type.toUpperCase()}
                          </span>
                          <span className="font-mono text-text-primary">
                            {action.ticker}
                          </span>
                          <span className="text-text-muted">
                            {action.quantity.toLocaleString()} shares
                          </span>
                          <ArrowRight className="w-4 h-4 text-text-muted" />
                          <span className="text-text-secondary text-sm">
                            {action.rationale}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Risks */}
                  {selectedScenario.risks.length > 0 && (
                    <div>
                      <h3 className="text-sm font-medium text-text-muted uppercase tracking-wider mb-3">
                        Risk Factors
                      </h3>
                      <ul className="space-y-1">
                        {selectedScenario.risks.map((risk, idx) => (
                          <li key={idx} className="flex items-center gap-2 text-sm">
                            <AlertTriangle className="w-3 h-3 text-warning" />
                            <span className="text-text-secondary">{risk}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Approval */}
                  <div className="pt-4 border-t border-border-subtle space-y-3">
                    {/* Error Message */}
                    {approvalError && (
                      <div className="flex items-center gap-2 p-3 bg-error/10 border border-error/20 rounded-lg">
                        <XCircle className="w-4 h-4 text-error shrink-0" />
                        <span className="text-sm text-error">{approvalError}</span>
                        <button
                          onClick={() => setApprovalError(null)}
                          className="ml-auto text-error hover:text-error/80"
                        >
                          <XCircle className="w-4 h-4" />
                        </button>
                      </div>
                    )}

                    <div className="flex items-center justify-between">
                      {isCurrentScenarioApproved ? (
                        <div className="flex items-center gap-3 w-full">
                          <div className="flex items-center gap-2 text-success">
                            <Check className="w-5 h-5" />
                            <span className="font-medium">Approved</span>
                          </div>
                          {currentApprovalInfo && (
                            <span className="text-xs text-text-muted font-mono">
                              Merkle: {currentApprovalInfo.merkleHash.slice(0, 16)}...
                            </span>
                          )}
                        </div>
                      ) : (
                        <>
                          <span className="text-sm text-text-muted">
                            Approval will be logged to Merkle chain
                          </span>
                          <button
                            onClick={() => setShowConfirmDialog(true)}
                            disabled={isApproving}
                            className="btn-primary flex items-center gap-2"
                          >
                            {isApproving ? (
                              <>
                                <Loader2 className="w-4 h-4 animate-spin" />
                                Approving...
                              </>
                            ) : (
                              'Approve Scenario'
                            )}
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      )}
    </div>
  )
}

interface MetricPillProps {
  icon: React.ElementType
  label: string
  value: number
}

function MetricPill({ icon: Icon, label, value }: MetricPillProps) {
  // Clamp value between 0 and 10
  const clampedValue = Math.max(0, Math.min(10, value))

  const getColor = () => {
    if (clampedValue >= 7) return 'text-success'
    if (clampedValue >= 5) return 'text-warning'
    return 'text-error'
  }

  return (
    <div className="flex flex-col items-center p-3 bg-bg-tertiary rounded-md">
      <Icon className={`w-4 h-4 mb-1 ${getColor()}`} />
      <span className={`text-lg font-bold ${getColor()}`}>{clampedValue.toFixed(1)}</span>
      <span className="text-xs text-text-muted">{label}</span>
    </div>
  )
}
