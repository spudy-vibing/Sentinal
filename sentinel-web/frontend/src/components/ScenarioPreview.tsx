import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Link } from 'react-router-dom'
import { GitBranch, Sparkles, ArrowRight, ChevronRight, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { useActivityStore } from '../stores/activityStore'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface Scenario {
  id: string
  title: string
  description: string
  score: number
  is_recommended: boolean
  actions?: Array<{
    type: string
    ticker: string
    quantity: number
  }>
}

export default function ScenarioPreview() {
  const [apiScenarios, setApiScenarios] = useState<Scenario[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const { scenarios: storeScenarios } = useActivityStore()

  // Use real-time scenarios from WebSocket if available, otherwise fall back to API
  const scenarios = storeScenarios.length > 0 ? storeScenarios.slice(0, 3) : apiScenarios

  // Debug logging - only when scenarios change
  useEffect(() => {
    if (storeScenarios.length > 0) {
      console.log('[ScenarioPreview] Real-time scenarios received:', storeScenarios)
    }
  }, [storeScenarios])

  useEffect(() => {
    fetchScenarios()
  }, [])

  const fetchScenarios = async () => {
    try {
      const response = await fetch(`${API_URL}/api/scenarios`)
      if (response.ok) {
        const data = await response.json()
        setApiScenarios(data.slice(0, 3)) // Show top 3
      }
    } catch (err) {
      console.error('Failed to fetch scenarios:', err)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="card">
      <div className="p-4 border-b border-border-subtle flex items-center justify-between">
        <h3 className="font-medium text-text-primary flex items-center gap-2">
          <GitBranch className="w-4 h-4 text-accent" />
          Top Scenarios
        </h3>
        <Link to="/scenarios" className="text-sm text-accent hover:text-accent-400 flex items-center gap-1">
          View All
          <ChevronRight className="w-4 h-4" />
        </Link>
      </div>

      <div className="p-4">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="terminal-cursor" />
            <span className="ml-3 text-text-muted">Loading scenarios...</span>
          </div>
        ) : scenarios.length === 0 ? (
          <div className="text-center py-8">
            <GitBranch className="w-8 h-8 text-text-muted mx-auto mb-2" />
            <p className="text-sm text-text-muted">No scenarios generated yet</p>
            <p className="text-xs text-text-muted">Inject an event to trigger scenario analysis</p>
          </div>
        ) : (
          <AnimatePresence mode="popLayout">
            <div className="grid grid-cols-3 gap-4">
              {scenarios.map((scenario, index) => (
                <motion.div
                  key={scenario.id}
                  initial={{ opacity: 0, y: 20, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  transition={{ delay: index * 0.1 }}
                  className={`p-4 rounded-lg border transition-all cursor-pointer hover:shadow-card-hover ${
                    scenario.is_recommended
                      ? 'bg-accent/5 border-accent/30 shadow-glow'
                      : 'bg-bg-tertiary border-border-subtle hover:border-border-default'
                  }`}
                >
                  <div className="flex items-center justify-between mb-3">
                    {scenario.is_recommended && (
                      <span className="badge-accent">
                        <Sparkles className="w-3 h-3" />
                        Recommended
                      </span>
                    )}
                    <span className={`text-2xl font-bold ${scenario.is_recommended ? 'text-accent' : 'text-text-primary'}`}>
                      {scenario.score.toFixed(1)}
                    </span>
                  </div>

                  <h4 className="font-medium text-text-primary mb-2">{scenario.title}</h4>
                  <p className="text-sm text-text-secondary line-clamp-2">
                    {scenario.description}
                  </p>

                  {/* Actions Preview */}
                  {scenario.actions && scenario.actions.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-border-subtle">
                      <div className="flex flex-wrap gap-1.5">
                        {scenario.actions.slice(0, 3).map((action, idx) => (
                          <span
                            key={idx}
                            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${
                              action.type === 'sell' || action.type === 'SELL'
                                ? 'bg-error/10 text-error'
                                : action.type === 'buy' || action.type === 'BUY'
                                ? 'bg-success/10 text-success'
                                : 'bg-info/10 text-info'
                            }`}
                          >
                            {(action.type === 'sell' || action.type === 'SELL') && <TrendingDown className="w-3 h-3" />}
                            {(action.type === 'buy' || action.type === 'BUY') && <TrendingUp className="w-3 h-3" />}
                            {(action.type === 'hold' || action.type === 'HOLD') && <Minus className="w-3 h-3" />}
                            {action.ticker}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="mt-4 flex items-center text-sm text-accent">
                    <span>View Details</span>
                    <ArrowRight className="w-3 h-3 ml-1" />
                  </div>
                </motion.div>
              ))}
            </div>
          </AnimatePresence>
        )}
      </div>
    </div>
  )
}
